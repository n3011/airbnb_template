from cassandra.cluster import Cluster
import logging
import time
import uuid

log = logging.getLogger()
log.setLevel('INFO')

class SimpleClient:
    session = None

    def connect(self, nodes):
        cluster = Cluster(nodes)
        metadata = cluster.metadata
        self.session = cluster.connect()
        log.info('Connected to cluster: ' + metadata.cluster_name)
        for host in metadata.all_hosts():
            log.info('Datacenter: %s; Host: %s; Rack: %s',
                host.datacenter, host.address, host.rack)

    def close(self):
        self.session.cluster.shutdown()
        self.session.shutdown()
        log.info('Connection closed.')


    def create_schema(self):
        #self.session.execute("""CREATE KEYSPACE nehome WITH replication = {'class':'NetworkTopologyStrategy', 'datacenter1':3};""")
        '''self.session.execute("""
            CREATE TYPE nehome.address (
                street text,
                landmark text,
                state text,
                country text,
                zipcode int);
            """)'''
        self.session.execute("""
            CREATE TABLE nehome.users (
                email text,
                username text,
                id uuid,
                firstname text,
                lastname text,
                contact set<varint>,
                age int,
                gender text,
                uaddress frozen<address>,
                joined date,
                pimage text,
                description text,
                PRIMARY KEY(email, username, joined)
            );
        """)


    def load_data(self):
        self.session.execute("""
            INSERT INTO nehome.users (email, username, id, firstname,lastname,joined)
            VALUES (
                 'ishant@gmail.com',
                'ishant',
                uuid(),
                'ishant',
                'mrinal',
                '05099999888'
            );
        """)
        log.info('Data loaded.')
    
    def query_schema(self):
        results = self.session.execute("""
    SELECT * FROM simplex.playlists
    WHERE id = 2cc9ccb7-6221-4ccb-8387-f22b6a1b354d;
""")
        print "%-30s\t%-20s\t%-20s\n%s" % \
    ("title", "album", "artist",
        "-------------------------------+-----------------------+--------------------")
        for row in results:
            print "%-30s\t%-20s\t%-20s" % (row.title, row.album, row.artist)
        log.info('Schema queried.')

def main():
    logging.basicConfig()
    client = SimpleClient()
    client.connect(['127.0.0.1'])
    client.create_schema()
    time.sleep(10)
    client.load_data()
    client.query_schema()
    client.close()

if __name__ == "__main__":
    main()
