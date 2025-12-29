from flask import Flask
from prometheus_client import (CollectorRegistry, Info, Gauge, generate_latest, CONTENT_TYPE_LATEST)
from redfish import redfish_client

# Eventually replace this with query parameters
from os import getenv
from dotenv import load_dotenv
load_dotenv()

# Setup
app = Flask(__name__)
PROM_NAMESPACE = getenv('PROM_NAMESPACE', 'redfish')

@app.route(getenv('PROM_ENDPOINT', '/metrics'))
def metrics():
    with redfish_client(base_url=getenv('REDFISH_HOST', 'http://127.0.0.1'), username=getenv('REDFISH_USER'), password=getenv('REDFISH_PASS'), timeout=5) as rf:
        promReg = CollectorRegistry()

        # Set our OEM variable
        # Reference (HPE): https://servermanagementportal.ext.hpe.com/docs/redfishservices/ilos/ilo5/ilo5_309/ilo5_resmap309/
        # Reference (Dell): https://developer.dell.com/apis/2978/versions/6.xx/openapi.yaml
        try:
            if len(rf.root['Oem'].keys()) > 1:
                print('More than 1 OEM found (%s), going with first one (%s)' % (', '.join(rf.root['Oem'].keys().upper()), next(iter(rf.root['Oem'].keys())).upper()))
            strOEM = next(iter(rf.root['Oem'].keys())).upper()
        except KeyError: # Only generic information is available
            strOEM = None
        
        # Baseline data
        match strOEM:
            case 'DELL':
                strIdentityType  = 'servicetag'
                strIdentityValue = rf.root['Oem']['Dell']['ServiceTag']
            case 'HPE':
                strIdentityType  = 'servername'
                strIdentityValue = rf.root['Oem']['Hpe']['Sessions']['ServerName']
            case _:
                strIdentityType  = 'none'
                strIdentityValue = 'none'
        Info('hardware', 'Basic Redfish Information (Vendor, Product, Version, Identification)', namespace=PROM_NAMESPACE, registry=promReg).info({
            'vendor'         : rf.root['Vendor'],
            'product'        : rf.root['Product'],
            'redfish_version': rf.root['RedfishVersion'],
            'identity_type'  : strIdentityType,
            'identity_value' : strIdentityValue
        })

        data = rf.get('/redfish/v1/Fabrics').dict
        if data != {}:
            None #TODO: Fabrics/Switches/#/Ports/#
        
        data = rf.get('/redfish/v1/SessionService').dict
        if data != {}:
            data = rf.get('/redfish/v1/SessionService/Sessions').dict
            Gauge('sessions_total', 'Number of active Redfish sessions', namespace=PROM_NAMESPACE, registry=promReg).set(data['Members@odata.count'])

        data = rf.get('/redfish/v1/TaskService').dict
        if data != {}:
            data = rf.get('/redfish/v1/TaskService/Tasks').dict
            Gauge('tasks_total', 'Number of active tasks', namespace=PROM_NAMESPACE, registry=promReg).set(data['Members@odata.count'])
            #TODO: TaskService/Tasks/#

        data = rf.get('/redfish/v1/Chassis').dict
        if data != {} and data['Members@odata.count'] > 0:
            for member in data['Members']:
                data = rf.get(member['@odata.id']).dict
                match data['ChassisType']:
                    case 'RackMount':
                        None
                    case 'StorageEnclosure':
                        # TODO: Anything cool here?
                        continue
                # Gauge: PowerState (Off,On)
                # Gauge: IndicatorLED (Off,On)
                # Gauge: LocationIndicatorActive (False,True)
                match strOEM:
                    case 'HPE':
                        for battery in data['Oem']['Hpe']['SmartStorageBattery']:
                            Gauge(f'chassis_{strOEM.lower()}_smartstoragebattery_charge_percent', f'{battery['ProductName'].strip()} charge level', ['index'], namespace=PROM_NAMESPACE, registry=promReg).labels(battery['Index']).set(battery['ChargeLevelPercent']/100)
                            Gauge(f'chassis_{strOEM.lower()}_smartstoragebattery_remaining_time', f'{battery['ProductName'].strip()} remaining charge time in seconds', ['index'], namespace=PROM_NAMESPACE, registry=promReg).labels(battery['Index']).set(battery['RemainingChargeTimeSeconds'])
                        sysmaintsw = Gauge(f'chassis_{strOEM.lower()}_system_maintence_switches', 'System Maintenance Switches', ['switch'], namespace=PROM_NAMESPACE, registry=promReg)
                        for switch, value in data['Oem']['Hpe']['SystemMaintenanceSwitches'].items():
                            sysmaintsw.labels(switch[2:]).set(1 if value == 'On' else 0)
                        # Firmware versions
                power = rf.get(data['Power']['@odata.id']).dict
                match strOEM:
                    case 'HPE':
                        poweroem = Gauge(f'chassis_{strOEM.lower()}_powermetric', 'HPE Power Metrics', ['metric'], namespace=PROM_NAMESPACE, registry=promReg)
                        for metric, value in power['Oem']['Hpe']['PowerMetric'].items():
                            if type(value) == int: poweroem.labels(metric).set(value)
                therm = rf.get(data['Thermal']['@odata.id']).dict
                if len(therm['Fans']) > 0:
                    fangauge = Gauge(f'chassis_thermal_fans_reading_{therm['Fans'][0]['ReadingUnits'].lower()}', f'Current Fan reading, in {therm['Fans'][0]['ReadingUnits']}', ['id', 'name', 'context', 'health', 'location'], namespace=PROM_NAMESPACE, registry=promReg)
                    for fan in therm['Fans']:
                        match strOEM:
                            case 'HPE': strLoc = fan['Oem']['Hpe']['Location']
                            case _: strLoc = ''
                        fangauge.labels(fan['MemberId'], fan['Name'], fan['PhysicalContext'], fan['Status']['Health'], strLoc).set(fan['Reading']/(100 if fan['ReadingUnits'] == 'Percent' else 1))
                if len(therm['Temperatures']) > 0:
                    tempgaugecur = Gauge('chassis_thermal_temperature_current', 'Current Temperature reading, in celsius', ['id', 'name', 'context', 'health'], namespace=PROM_NAMESPACE, registry=promReg)
                    tempgaugethres = Gauge('chassis_thermal_temperature_threshold', 'Temperature thresholds, in celsius', ['id', 'threshold'], namespace=PROM_NAMESPACE, registry=promReg)
                    for temp in therm['Temperatures']:
                        if temp['Status']['State'] != 'Absent':
                            tempgaugecur.labels(temp['MemberId'], temp['Name'], temp['PhysicalContext'], temp['Status']['Health']).set(temp['ReadingCelsius'])
                            for thres in ['UpperThresholdCritical', 'UpperThresholdFatal']:
                                if temp[thres] != None: tempgaugethres.labels(temp['MemberId'], thres).set(temp[thres])
                adapters = rf.get(data['NetworkAdapters']['@odata.id']).dict
                if adapters != {} and adapters['Members@odata.count'] > 0:
                    for member in adapters['Members']:
                        adapters = rf.get(member['@odata.id']).dict
                        for controller in adapters['Controllers']:
                            adapter_location_id = controller['Location']['PartLocation']['LocationOrdinalValue']
                            adapter_location_name = controller['Location']['PartLocation']['ServiceLabel']
                            linkspeed = Gauge('chassis_networkadapter_linkspeed_current', 'Current NIC link speed, in Mbps', ['adapter_location_id', 'adapter_location_name', 'port_number'], namespace=PROM_NAMESPACE, registry=promReg)
                            linkstatus = Gauge('chassis_networkadapter_link_state', 'Current NIC state, 1=Up, 0=Down, -1=Unknown', ['adapter_location_id', 'adapter_location_name', 'port_number'], namespace=PROM_NAMESPACE, registry=promReg)
                            for networkport in controller['Links']['NetworkPorts']:
                                networkport = rf.get(networkport['@odata.id']).dict
                                portnumber = networkport['PhysicalPortNumber']
                                linkspeed.labels(adapter_location_id, adapter_location_name, portnumber).set(networkport['CurrentLinkSpeedMbps'])
                                match networkport['LinkStatus']:
                                    case 'Up': linkstatusval = 1
                                    case 'Down': linkstatusval = 0
                                    case _: linkstatusval = -1
                                linkstatus.labels(adapter_location_id, adapter_location_name, portnumber).set(linkstatusval)
                power = rf.get(data['Power']['@odata.id']).dict
                pwrctrlcapacity = Gauge('chassis_powercontrol_capacity', 'Total PowerControl capacity, in watts', ['id'], namespace=PROM_NAMESPACE, registry=promReg)
                pwrctrlconsumed = Gauge('chassis_powercontrol_consumed', 'Total PowerControl consumed, in watts', ['id'], namespace=PROM_NAMESPACE, registry=promReg)
                pwrctrllimit = Gauge('chassis_powercontrol_limit', 'PowerControl limit, in watts', ['id'], namespace=PROM_NAMESPACE, registry=promReg)
                for pwrctrl in power['PowerControl']:
                    pwrctrlcapacity.labels(pwrctrl['MemberId']).set(pwrctrl['PowerCapacityWatts'])
                    pwrctrlconsumed.labels(pwrctrl['MemberId']).set(pwrctrl['PowerConsumedWatts'])
                    pwrctrllimit.labels(pwrctrl['MemberId']).set(-1 if pwrctrl['PowerLimit']['LimitInWatts'] == None else pwrctrl['PowerLimit']['LimitInWatts'])
                match strOEM:
                    case 'HPE':
                        pwrsupplyambtemp = Gauge(f'chassis_powersupply_{strOEM.lower()}_ambienttemp', 'Power supply ambient temp, in celsius', [], namespace=PROM_NAMESPACE, registry=promReg)
                        pwrsupplycaps = Gauge(f'chassis_powersupply_{strOEM.lower()}_powercap', 'Power caps, in percent', ['cap'], namespace=PROM_NAMESPACE, registry=promReg)
                        pwrsupplyspecific = Gauge(f'chassis_powersupply_{strOEM.lower()}_powerzone', 'Power consumption for specific zones, in watts', ['zone'], namespace=PROM_NAMESPACE, registry=promReg)
                        pwrsupplyambtemp.set(power['Oem']['Hpe']['PowerMetric']['AmbTemp'])
                        for cap in ['Cap', 'CpuCapLim', 'CpuMax', 'CpuPwrSavLim']:
                            pwrsupplycaps.labels(cap.lower()).set(power['Oem']['Hpe']['PowerMetric'][cap])
                        for zone in ['CpuWatts', 'DimmWatts', 'GpuWatts']:
                            pwrsupplyspecific.labels(zone[:-5].lower()).set(power['Oem']['Hpe']['PowerMetric'][zone])
                pwrsupplyoutput = Gauge('chassis_powersupply_output', 'Power supply output, in watts', ['id', 'location', 'status'], namespace=PROM_NAMESPACE, registry=promReg)
                pwrsupplyinput = Gauge('chassis_powersupply_input', 'Power supply input voltage', ['id', 'location', 'status'], namespace=PROM_NAMESPACE, registry=promReg)
                pwrsupplycapacity = Gauge('chassis_powersupply_capacity', 'Power supply capacity, in watts', ['id', 'location', 'status'], namespace=PROM_NAMESPACE, registry=promReg)
                for pwrsupply in power['PowerSupplies']:
                    match strOEM:
                        case 'HPE':
                            pwrsupplylocation = f'Bay {pwrsupply['Oem']['Hpe']['BayNumber']}'
                        case _:
                            pwrsupplylocation = ''
                    pwrsupplyoutput.labels(pwrsupply['MemberId'], pwrsupplylocation, pwrsupply['Status']['Health']).set(pwrsupply['LastPowerOutputWatts'])
                    pwrsupplyinput.labels(pwrsupply['MemberId'], pwrsupplylocation, pwrsupply['Status']['Health']).set(pwrsupply['LineInputVoltage'])
                    pwrsupplycapacity.labels(pwrsupply['MemberId'], pwrsupplylocation, pwrsupply['Status']['Health']).set(pwrsupply['PowerCapacityWatts'])
        # Systems
    rf.logout()
    return generate_latest(registry=promReg), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Start the server
if __name__ == '__main__':
    try:
        app.run(host=getenv('FLASK_HOST', '127.0.0.1'), port=int(getenv('FLASK_PORT', 5000)), debug=getenv('FLASK_DEBUG', False))
    except Exception as e:
        print(f'Server failed to start: {e}')
        exit(1)