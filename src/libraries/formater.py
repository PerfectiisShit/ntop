

def format_request_status(data):
    if not data:
        return data

    status = {
        '2xx': {'count': 0, 'bandwidth': 0, 'details': []},
        '3xx': {'count': 0, 'bandwidth': 0, 'details': []},
        '4xx': {'count': 0, 'bandwidth': 0, 'details': []},
        '5xx': {'count': 0, 'bandwidth': 0, 'details': []},
        'total_counts': 0
    }
    for i in data:
        status['total_counts'] += i['count']
        for key in status.keys():
            if i[key] != 0:
                status[key]['count'] += i['count']
                status[key]['bandwidth'] += i['bandwidth']
                details = {'code': i['status'], 'bandwidth': i['bandwidth'], 'count': i['count']}
                status[key]['details'].append(details)

    return status


def format_request_path(data):
    if not data:
        return data

    for i in data:
        request = i['request'].split()
        if len(request) != 3:
            i['data'] = i['request']
            i['method'] = i['protocol'] = 'Unknown'
        else:
            i['method'] = request[0]
            i['data'] = request[1]
            i['protocol'] = request[2]

        del i['request']

    return data
