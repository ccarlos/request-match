from collections import defaultdict
from re import compile
from sys import argv, exit, stderr


class RequestMatch:
    N_DAYS = 20   # Total days
    N_SERV = 0.0  # Total services: updated in self.process_data()

    def __init__(self):
        """self data structures.

        self.categories:  category => [names of service providers]
        self.providers:   provider => [categories serviceable]
        self.requests:    req_name => {'catg': 'category',
                                       'days': [days serviceable],
                                       'last_d': int(last service day),
                                       'num_p': % prov's that can service req.
                                       'solved_by': 'name of provider',
                                       'solved_day': int,
                                      }
        """
        self.categories = {}
        self.providers = {}
        self.requests = {}
        self.solved_requests = []

    def valid_day_range(self, num):
        """Is num a valid number or number range? (e.g. 2 or 2-19)

        Also checks if num is in range of [1 - RequestMatch.N_DAYS].
        """
        p = compile('\d+-\d+|\d+')
        m = p.match(num)
        if m:
            num_list = num.split("-")

            # Check elements in num_list are in range.
            if len(num_list) == 2:
                return (len([n for n in num_list
                     if 1 <= int(n) <= RequestMatch.N_DAYS]) == 2)
            return (len([n for n in num_list
                 if 1 <= int(n) <= RequestMatch.N_DAYS]) == 1)
        return False

    def valid_service(self, line):
        """Does line have sufficient elements to be a service?"""
        if len(line) >= 3:
            return True
        return False

    def valid_request(self, line):
        """Does line have sufficient and valid elements to be a request?"""
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

        request_data = {'catg': catg, 'days': days_l, 'last_d': days_l[-1],
                        'num_p': 0, 'solved_by': '', 'solved_day': None}
        self.requests.setdefault(name, {}).update(request_data)

    def can_process(self):
        """Can self be processed in self.process_data()?"""
        if not (self.providers and self.requests):
            return False
        return True

    def rank_providers(self, day_requests):
        """List of providers ranked by the number of categories offered.

        day_requests: used to extract categories and rank providers.
        """
        d = defaultdict(int)  # d: provider => number of categories offered

        for r in day_requests:
            catg = r[1]['catg']
            for name in self.categories[catg]:
                d[name] += 1

        return [p[0] for p in sorted(d.iteritems(), key=lambda p: (p[1]))]

    def process_data(self):
        """Determine the number of requests that can be solved.

        # Definitions
        SOLVED - Set of all requests solved
        PROV - Set of all providers
        REQ - Set of all requests
            last_d - Last day REQ instance can be solved.
            num_p  - num PROV that can solve REQ instance / length of PROV

        SR <- order all requests in REQ by: last_d and num_p

        DAY_R <- subset of REQ, all REQ that can be solved in given day
        DAY_P <- subset of PROV, all PROV ranked by the number of requests
                 solvable in DAY_R

        # Algorithm
        SR
        for day in N_DAYS:
            DAY_R
            DAY_P
            for req in DAY_R
                If req can be solved by p in DAY_P
                    Remove p from DAY_P
                    Add req to SOLVED
                    Rem req from SR
                    break
        """
        if (len(self.providers) == 0 or len(self.requests) == 0):
            return

        # Update: N_SERV and num_p.
        # Can't assume services come before requests in inputfile.
        RequestMatch.N_SERV = float(len(self.providers))
        for k, v in self.requests.iteritems():
            self.requests[k]['num_p'] = (len(self.categories[v['catg']]) /
                                         RequestMatch.N_SERV)

        # Order requests by: last_d, num_p
        sorted_req = [r for r in self.requests.iteritems()]
        sorted_req.sort(key=lambda r: (r[1]['last_d'], r[1]['num_p']))

        # Go though days and for each try to solve requests for the given day.
        for day in xrange(1, RequestMatch.N_DAYS + 1):
            day_requests = [r for r in sorted_req if day in r[1]['days']]
            day_providers = self.rank_providers(day_requests)

            # loop day_requests and see if day_providers can solve.
            for r in day_requests:
                for prov in day_providers[:]:
                    if prov in self.categories[r[1]['catg']]:
                        # found a prov that can solve request r:
                        # update request and add to solved requests
                        r[1]['solved_by'] = prov
                        r[1]['solved_day'] = day
                        self.solved_requests.append(r)

                        # remove prov and request
                        day_providers.remove(prov)
                        sorted_req.remove(r)
                        break


def main(argv):
    """
    Usage: python request_matching.py inputfile

    See README for problem description.

    main() will read in lines from inputfile. Valid lines will be parsed and
    update the current object. A new object will be created for each problem
    identified by a blank line. Each problem  will be processed to determine
    the number of requests fulfilled. After processing we will add the problem
    to a list. Afterwards, we will iterate the list and determine the number
    of requests fulfilled for each problem.
    """
    if len(argv) != 1:
        print >> stderr, "Insufficient number of arguments."
        print >> stderr, "Usage: request_matching.py filename"
        exit(2)

    file_name = argv[0]

    # Each line is seperated by words.
    with open(file_name, 'r') as f:
        read_lines = [line.strip().split() for line in f.readlines()]
        read_lines.append([])  # EOF

    req_match_jobs = []
    # Reduce function references.
    append_job = req_match_jobs.append
    job = RequestMatch()

    # Analyze and parse valid lines.
    for line in read_lines:
        if not line:
            if job.can_process():
                job.process_data()
                append_job(job)
                job = RequestMatch()
            continue
        if line[0] == "service" and job.valid_service(line):
            job.parse_service(line)
        elif line[0] == "request" and job.valid_request(line):
            job.parse_request(line)

    for job in req_match_jobs:
        print len(job.solved_requests)


if __name__ == '__main__':
    exit(main(argv[1:]))
