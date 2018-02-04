"""
##            ###########
 ##          ##        ##
  ##        ##         ##
   ##      ##############
    ##    ##
     ##  ##
      ####

AUTHOR = Vimal Paliwal <paliwalvimal1993@gmail.com>

>> This script creates an encrypted AMI of your EC2 instance <<

MIT License

Copyright (c) 2018 Vimal Paliwal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import boto3
import uuid
import time
import sys
import datetime


def encrypt_ami(instance_id, ami_name = "", src_region = "us-east-1", dest_region = "", reboot_instance = True, kms_key_arn = ""):
    """
    :param instance_id: Instance ID to be encrypted
    :param ami_name: (Optional) AMI Name
    :param src_region: (Optional) Region where your instance sits. Default = us-east-1
    :param dest_region: (Optional) Region where you want the encrypted AMI to sit. Default = src_region
    :param reboot_instance: (Optional) Whether you want the EC2 instance to be rebooted while creating the AMI
    :param kms_key_arn: (Optional) ARN of KMS Key
    :return: Encrypted AMI ID
    """

    response = ""

    if dest_region.strip() == "":
        dest_region = src_region

    if ami_name.strip() == "":
        ami_name = "ami_" + str(uuid.uuid4())

    ec2 = boto3.client("ec2")

    start = datetime.datetime.now().replace(microsecond=0)
    # ======Creating unencrypted AMI======
    print("Creating AMI", end="")
    sys.stdout.flush()
    response = ec2.create_image(
        Description='Unencrypted AMI of ' + instance_id,
        InstanceId=instance_id,
        Name=ami_name,
        NoReboot=reboot_instance
    )
    u_ami_id = response["ImageId"]

    # ======Waiting while the unencrypted AMI is available to use======
    while True:
        print(".", end="")
        sys.stdout.flush()
        response = ec2.describe_images(
            ImageIds=[
                u_ami_id,
            ]
        )
        if response["Images"][0]["State"] == "available":
            break

        time.sleep(0.5)

    # ======Creating encrypted AMI======
    print()
    print("Encrypting AMI", end="")
    sys.stdout.flush()
    ec2_copy = boto3.client("ec2", region_name = dest_region)
    if kms_key_arn.strip() == "":
        response = ec2_copy.copy_image(
            Description='Encrypted AMI of ' + instance_id,
            Encrypted=True,
            Name='encrypted_' + ami_name,
            SourceImageId=u_ami_id,
            SourceRegion=src_region
        )
    else:
        response = ec2_copy.copy_image(
            Description='Encrypted AMI of ' + instance_id,
            Encrypted=True,
            Name='encrypted_' + ami_name,
            KmsKeyId=kms_key_arn,
            SourceImageId=u_ami_id,
            SourceRegion=src_region
        )
    e_ami_id = response["ImageId"]

    # ======Waiting while the encrypted AMI is available to use======
    while True:
        print(".", end="")
        sys.stdout.flush()
        response = ec2.describe_images(
            ImageIds=[
                e_ami_id,
            ]
        )
        if response["Images"][0]["State"] == "available":
            break

        time.sleep(0.5)

    # ======Removing the unencrypted AMI======
    ec2.deregister_image(
        ImageId=u_ami_id
    )

    end = datetime.datetime.now().replace(microsecond=0)
    print()
    print("AMI Created. AMI Id: " + e_ami_id)
    print("Time taken: " + str(end-start))

    return e_ami_id
