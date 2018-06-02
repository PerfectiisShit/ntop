from libraries.utils import bytes2human


def format_request_status(data):
    if not data:
        return data

    status = {
        '2xx': {'count': 0, 'bandwidth': 0, 'data': '2xx Success', 'details': []},
        '3xx': {'count': 0, 'bandwidth': 0, 'data': '3xx Redirection', 'details': []},
        '4xx': {'count': 0, 'bandwidth': 0, 'data': '4xx Client Error', 'details': []},
        '5xx': {'count': 0, 'bandwidth': 0, 'data': '5xx Server Error', 'details': []},
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


def format_request_path(data, total_requests):
    _data = []
    if not data:
        return _data

    for i in data:
        request = i['request'].split()
        if len(request) != 3:
            i['data'] = i['request']
            i['method'] = i['protocol'] = 'Unknown'
        else:
            i['method'], i['data'], i['protocol'] = request

        message = "{:<5} {:>6,.2%} {:>12}  {:<8} {:<9} {}" \
            .format(i['count'],
                    float(i['count'] / total_requests),
                    bytes2human(i['bandwidth']),
                    i['method'],
                    i['protocol'],
                    i['data'])
        _data.append(message)

    return _data
