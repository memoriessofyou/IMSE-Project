# IMSE-Project
#  DataShift: RDBMS to NoSQL Migration Engine

**A containerized full-stack application that models a complex relational database and executes a live, one-way migration to a schemaless NoSQL architecture**. Built entirely without ORMs to demonstrate fundamental data modeling and cross-paradigm performance tuning.

### Tech Stack
* **Infrastructure:** Docker, Debian 12
* **Databases:** MariaDB (SQL), MongoDB (NoSQL)
* **Architecture:** 3NF Relational modeling, N-side referencing NoSQL

###  Key Features
* **Automated Seeding:** One-click GUI generation of randomized, relational test data.
* **Live Migration Protocol:** Safely maps SQL data to MongoDB, preserves semantic relationships, and automatically severs the SQL connection upon completion.
* **High-Frequency Writes:** Engineered backend designed to simulate heavy-write operations across complex, existence-dependent entities.
* **Performance Analytics:** Translates multi-join SQL reports into MongoShell, utilizing custom indexing to optimize read execution times.

###  Quick Start
1. Run `docker-compose up --build`.
2. Access the web GUI.
3. Click **"Initialize SQL Database"**.
4. Click **"Execute Migration"**.
