insert into roomads (district, pricemonth, posted, minlease,
        street,locality,zipcode, uid) values('kamrup', 2000, 1101919292933992,
                6, 'beltola road', 'basistah chariali', 781029, uuid()) ;
        cqlsh:nehome> select * from roomads  ;

        insert into users (email, username, joined, age, id)
        values('ishantim@gmail.com', 'ishant', '2016-01-01', 21,
                '9827363273673273233') ;



update temporoom set images=['test1.jpg', 'test2.jpg'] where dostrict='Kamrup' and zipcode=781009 and rest of the primary key
