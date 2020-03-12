# Long Beach

### Start a local stack

More Info: ([https://wiki.openlattice.com/display/ENGR/Running+the+production+environment+locally](https://wiki.openlattice.com/display/ENGR/Running+the+production+environment+locally))

1. `elasticsearch -E cluster.name=openlattice`
2. Start Conductor and wait for the banner
3. Start Datastore and wait for the banner
4. Run gallery locally from within its directory `npm run app`
5. Create a test database and table lb_demo:

        createdb test
        psql test
        
        test=# create user username with password 'password'; 

6. Get JWT from [http://localhost:9090/gallery/#/edit_account](http://localhost:9090/gallery/#/edit_account)
7. From  inside the unzipped directory, run `python make_ents.py` .  It will ask you for your jwt -  copy and paste into the terminal. This script will create the entity sets needed on [localhost](http://localhost) based on what is needed from the flight. It will display the names of entity sets as it creates them and then some 500 errors when it attempts to create the same entity set more than once - these can be ignored.
8. Next, run `lb_demo.py` . This creates the demo data table and puts it  into a new table in the db we just created. 
9. With Conductor and Datastore running, and entities created, run Shuttle (main class `com.openlattice.shuttle.ShuttleCliKt`) with the following arguments: 

        --flight
        path/to/unzip/dir/lb_demo.yaml
        --token
        *** (your jwt)
        --sql
        "select * from lb_demo;"
        --config
        path/to/unzip/dir/localmapper.yaml
        --fetchsize
        2000
        --upload-size
        2000
        --datasource
        test
        --environment
        LOCAL
