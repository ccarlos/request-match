import sys


class RequestMatch:
    """ """
    N_DAYS = 20  # Days total.
    N_SERV = 0.0  # Services total.

    def __init__(self):
        self.categories = {}  # catg => [names of service providers]
        self.providers = {}   # prov => [categories servicable]
        self.requests = {}    # req_name => {'catg': 'category',
                              #              'days': [days serviceable],
                              #              'last_d': int(last service day),
                              #              'num_p': % prov that can service
                              #              #prov that can service/total prov
                              #             }

    def valid_day_range(self, num):
        """Is num a valid number or number range? e.g. 2 or 2-19

        Also checks if num is in range of [1 - Request.Match.N_DAYS].
        """
        import re
        p = re.compile('\d+-\d+|\d+')
        m = p.match(num)
        if m:
            num_list = num.split("-")

            # Check num_list is in range.
            if len(num_list) == 2:
                return (len([n for n in num_list
                     if 1 <= int(n) <= RequestMatch.N_DAYS]) == 2)
            return (len([n for n in num_list
                 if 1 <= int(n) <= RequestMatch.N_DAYS]) == 1)
        return False

    def valid_service(self, line):
        """Does line have sufficient arguments to be a service?"""
        if len(line) >= 3:
            return True
        return False

    def valid_request(self, line):
        """Does line have sufficient and valid arguments to be a request?"""
        if len(line) == 4 and self.valid_day_range(line[-1]):
            return True
        return False

    def parse_service(self, line):
        """Parse service line and fill appropriate service provider data."""
        provider = line[1]
        for catg in line[2:]:
            self.categories.setdefault(catg, []).append(provider)
            self.providers.setdefault(provider, []).append(catg)

    def parse_request(self, line):
        """Parse request line and fill appropriate request data."""
        name = line[1]
        catg = line[2]
        days = [int(n) for n in line[3].split("-")]  # convert days to ints
        days_l = ([days[0]] if len(days) == 1
                            else range(days[0], days[1] + 1))

        # processing to calc: num_p
        request_data = {'catg': catg, 'days': days_l, 'last_d': days_l[-1],
                        'num_p': 0}
        self.requests.setdefault(name, {}).update(request_data)

    def can_process(self):
        """Can self be processed in self.processs_data?"""
        if not (self.providers and self.requests):
            return False
        return True

    def rank_providers(self, day_requests):
        """List of providers ranked by the number of services offered.

        day_requests: used to extract categories and rank providers.
        """
        from collections import defaultdict
        d = defaultdict(int)  # d: provider => number of categories

        for r in day_requests:
            catg = r[1]['catg']
            for name in self.categories[catg]:
                d[name] += 1

        return [x[0] for x in sorted(d.iteritems(), key=lambda x: (x[1]))]

    def process_data(self):
        if (len(self.providers) == 0 or len(self.requests) == 0):
            return

        # Update: N_SERV and num_p.
        # Can't assume services come before requests.
        RequestMatch.N_SERV = float(len(self.providers))
        for k, v in self.requests.iteritems():
            self.requests[k]['num_p'] = (len(self.categories[v['catg']]) /
                                         RequestMatch.N_SERV)

        # Order requests by: last_d, num_p
        sorted_req = [x for x in self.requests.iteritems()]
        sorted_req.sort(key=lambda x: (x[1]['last_d'], x[1]['num_p']))

        # Go though days and for each try to solve requests for the given day.
        for day in range(1, RequestMatch.N_DAYS + 1):
            day_requests = [r for r in sorted_req if day in r[1]['days']]
            day_providers = self.rank_providers(day_requests)

            # loop day_requests and see if day_providers can solve. 
            for r in day_requests:
                for prov in day_providers[:]:
                    if prov in self.categories[r[1]['catg']]:
                        # found a match: remove prov from day and request
                        # request(sorted_req)
                        print "**********SOLVED************"
                        print "%s solved %s on day: %d" % (prov, r, day)
                        day_providers.remove(prov)
                        sorted_req.remove(r)
                        break


def main(argv):
    if len(argv) != 1:
        print >> sys.stderr, "Insufficient number of arguments."
        print >> sys.stderr, "Usage: request_matching.py filename"
        sys.exit(2)

    file_name = argv[0]

    # Each line is read and seperated by words and appended to read_lines.
    with open(file_name, 'r') as f:
        read_lines = [line.strip().split() for line in f.readlines()]
        read_lines.append([])  # EOF

    req_match_jobs = []
    obj = RequestMatch()
    for line in read_lines:
        if not line:
            print "empty ----------"
            #if obj.can_process():
            #    req_match_jobs.append(obj)
            #    obj = RequestMatch()
            continue
        if line[0] == "service" and obj.valid_service(line):
            obj.parse_service(line)
        elif line[0] == "request" and obj.valid_request(line):
            obj.parse_request(line)
        # invalid lines are ignored

    print obj.categories
    print
    print obj.requests
    print
    print obj.providers
    print
    obj.process_data()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))