import boto3
from datetime import *
import sys
import os



class Logs(object):


    def __init__(self, log_group, start_timestamp, end_timestamp):
        self.client = boto3.client('logs')
        self.log_group = log_group
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.stream_list = []
        self.file_name = "./log/{}_{}.log".format(self.log_group.replace('/', '_'), str(self.start_timestamp))

        if os.path.isfile(self.file_name):
            os.remove(self.file_name)



    def get_stream(self, token=None):
        params = {
                    'logGroupName': self.log_group,
                    'orderBy': 'LastEventTime',
                    'descending': True
                }
        if token is not None:
            params.update({'nextToken': token})

        return self.client.describe_log_streams(**params)



    def check_stream(self, stream):
        for st in stream['logStreams']:

            if self.start_timestamp >= st['firstEventTimestamp']:
                return

            if self.end_timestamp is None:
                self.append_stram(st['logStreamName'])
            else:
                if  self.end_timestamp >= st['lastEventTimestamp']:
                    self.append_stram(st['logStreamName'])


        if 'nextToken' not in stream:
            return

        next_token = stream['nextToken']
        self.check_stream(self.get_stream(next_token))


    def append_stram(self, val):
        self.stream_list.append(val)


    def get_log(self, stream, token):
        params = {
                    'logGroupName': self.log_group,
                    'logStreamName': stream,
                    'startFromHead': True
                }
        if token is not None:
            params.update({'nextToken': token})

        return self.client.get_log_events(**params)


    def check_log(self):

        for stream in self.stream_list:
            self.dump("##### {} #####\n".format(stream))
            self.dump_log(stream)


    def dump_log(self, stream, token=None, last_token=None):

        log = self.get_log(stream, token)

        for event in log['events']:
            self.dump(event['message'])


        if log['nextForwardToken'] != last_token:
            self.dump_log(stream, log['nextForwardToken'], token)



    def dump(self, val):
        with open(self.file_name, 'a') as f:
            f.write(val)







def get_timestamp(t):
    if t is None:
        return None

    epoc = datetime(1970, 1, 1)
    return (datetime.strptime(t, '%Y/%m/%dT%H:%M') - epoc).total_seconds() * 1000



def main(log_group_name, start_time, end_time):

    start_timestamp = get_timestamp(start_time)
    end_timestamp = get_timestamp(end_time)

    log = Logs(log_group_name, start_timestamp, end_timestamp)
    stream = log.get_stream()
    log.check_stream(stream)
    log.check_log()





if __name__ == '__main__':


    if len(sys.argv) < 3:
        error = "ERROR: Please enter  log group name and start date\n"
        command = "{} python {} [log group name] [%Y/%m/%dT%H:%M]".format(error, sys.argv[0])
        print(command)
        exit()


    log_group_name = sys.argv[1]
    start_time = sys.argv[2]

    if len(sys.argv) > 3:
        end_time = sys.argv[3]
    else:
        end_time = None



    main(log_group_name, start_time, end_time)

