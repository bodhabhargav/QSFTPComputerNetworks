#QSFTP (Quick Secure File Transfer Protocol)
QSFTP is a file transfer protocol built upon QUIC using Python and the aioquic library. It ensures secure and efficient file transfers.

#Prerequisites
Python 3.x
aioquic library
You can install the necessary Python libraries using:


pip install aioquic
#Generating Certificates
To generate the necessary certificates, download the san.cnf configuration file and execute the following command:

openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 365
#Prompt Questions
When you execute the command, you will be prompted to enter information for the certificate request. You can use the following example responses:

Country Name (2 letter code) [AU]: US
State or Province Name (full name) [Some-State]: Pennsylvania
Locality Name (eg, city) []: Philadelphia
Organization Name (eg, company) [Internet Widgits Pty Ltd]: Drexel
Organizational Unit Name (eg, section) []: .
Common Name (e.g. server FQDN or YOUR name) []: Bodha Bhargav
Email Address []: by338@drexel.edu
After these questions are answered, cert.pem and key.pem will be generated.

#Running the Python Scripts
Starting the Server
First, start the server by executing the qsftp_server.py script. The server will listen on port 5000 unless you change it in line 79.
python qsftp_server.py

#Running the Client
Next, run the client by executing the qsftp_client.py script. In line 52 of the script, specify the file you want to transfer. Ensure that the program has the necessary permissions to access the file.
python qsftp_client.py

#File Transfer
When qsftp_client.py is successfully executed, the specified file will be transferred to the directory where qsftp_server.py is located. The received file will be named received_file.txt.

#Verifying File Integrity
To verify that the file has been transferred correctly, you can compare the checksums (MD5) of the original file and the received file:


md5sum original_file.txt
md5sum received_file.txt
If the checksums match, the file has been transferred successfully.
