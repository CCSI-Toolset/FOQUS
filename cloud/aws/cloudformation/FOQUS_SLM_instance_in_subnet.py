#!/usr/bin/python
# -*- coding: utf-8 -*-
#################################################################################
# FOQUS Copyright (c) 2012 - 2023, by the software owners: Oak Ridge Institute
# for Science and Education (ORISE), TRIAD National Security, LLC., Lawrence
# Livermore National Security, LLC., The Regents of the University of
# California, through Lawrence Berkeley National Laboratory, Battelle Memorial
# Institute, Pacific Northwest Division through Pacific Northwest National
# Laboratory, Carnegie Mellon University, West Virginia University, Boston
# University, the Trustees of Princeton University, The University of Texas at
# Austin, URS Energy & Construction, Inc., et al.  All rights reserved.
#
# Please see the file LICENSE.md for full copyright and license information,
# respectively. This file is also available online at the URL
# "https://github.com/CCSI-Toolset/FOQUS".
#################################################################################
# Converted from VPC_With_VPN_Connection.template located at:
# http://aws.amazon.com/cloudformation/aws-cloudformation-templates
import optparse

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from troposphere import Base64, FindInMap, GetAtt, Join, Output
from troposphere import Parameter, Ref, Tags, Template
from troposphere.autoscaling import Metadata
from troposphere.ec2 import (
    PortRange,
    NetworkAcl,
    Route,
    VPCGatewayAttachment,
    SubnetRouteTableAssociation,
    Subnet,
    RouteTable,
    VPC,
    NetworkInterfaceProperty,
    NetworkAclEntry,
    SubnetNetworkAclAssociation,
    EIP,
    Instance,
    InternetGateway,
    SecurityGroupRule,
    SecurityGroup,
)
from troposphere.policies import CreationPolicy, ResourceSignal
from troposphere.cloudformation import (
    Init,
    InitFile,
    InitFiles,
    InitConfig,
    InitService,
    InitServices,
)


from troposphere import iam

# from troposphere.iam import Role, InstanceProfile
from awacs.aws import Allow, Statement, Principal, Policy, Action
from awacs.sts import AssumeRole


# Globals
# bucket_name:
#   used by instance cloud-init scripts to grab installers, etc
BUCKET_NAME = None
CONFIG_FILE = "foqus_templates.cfg"
ADMIN_PASSWORD = None


def _create_template(
    vpc_id, subnet_public_id, internetgateway_id, network_interface_id, allocation_id
):
    """returns Template instance"""
    t = Template()
    t.add_version("2010-09-09")
    t.add_description(
        """Template to create SLM instance and bind to
    passed in Network Interface\
    """
    )

    keyname_param = t.add_parameter(
        Parameter(
            "KeyName",
            ConstraintDescription="must be the name of an existing EC2 KeyPair.",
            Description="Name of an existing EC2 KeyPair to enable SSH access to \
    the instance",
            Type="AWS::EC2::KeyPair::KeyName",
        )
    )

    sshlocation_param = t.add_parameter(
        Parameter(
            "RDPLocation",
            Description=" The IP address range that can be used to RDP to the EC2 \
    instances",
            Type="String",
            MinLength="9",
            MaxLength="18",
            Default="0.0.0.0/0",
            AllowedPattern=r"(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})",
            ConstraintDescription=(
                "must be a valid IP CIDR range of the form x.x.x.x/x."
            ),
        )
    )

    instanceType_param = t.add_parameter(
        Parameter(
            "InstanceType",
            Type="String",
            Description="SLM Server EC2 instance type",
            Default="t2.micro",
            AllowedValues=[
                "t1.micro",
                "t2.micro",
                "t2.small",
                "t2.medium",
                "t3.micro",
                "t3.small",
                "t3.medium",
                "t3.large",
                "t3.xlarge",
            ],
            ConstraintDescription="must be a valid EC2 instance type.",
        )
    )

    t.add_mapping(
        "AWSInstanceType2Arch",
        {
            "t1.micro": {"Arch": "PV64"},
            "t2.micro": {"Arch": "HVM64"},
            "t2.small": {"Arch": "HVM64"},
            "t2.medium": {"Arch": "HVM64"},
            "t3.micro": {"Arch": "HVM64"},
            "t3.small": {"Arch": "HVM64"},
            "t3.medium": {"Arch": "HVM64"},
            "t3.large": {"Arch": "HVM64"},
            "t3.xlarge": {"Arch": "HVM64"},
        },
    )

    # Windows_Server-2016-English-Full-Base-2018.09.15
    t.add_mapping(
        "AWSRegionArch2AMI", {"us-east-1": {"HVM64": "ami-01945499792201081"}}
    )

    ref_stack_id = Ref("AWS::StackId")
    ref_region = Ref("AWS::Region")
    ref_stack_name = Ref("AWS::StackName")

    routeTable = t.add_resource(
        RouteTable("RouteTable", VpcId=vpc_id, Tags=Tags(Application=ref_stack_id))
    )

    route = t.add_resource(
        Route(
            "Route",
            # DependsOn='AttachGateway',
            GatewayId=internetgateway_id,
            DestinationCidrBlock="0.0.0.0/0",
            RouteTableId=Ref(routeTable),
        )
    )

    subnetRouteTableAssociation = t.add_resource(
        SubnetRouteTableAssociation(
            "SubnetRouteTableAssociation",
            SubnetId=subnet_public_id,
            RouteTableId=Ref(routeTable),
        )
    )

    """
    networkAcl = t.add_resource(
        NetworkAcl(
            'NetworkAcl',
            VpcId=vpc_id,
            Tags=Tags(
                Application=ref_stack_id),
        ))

    inBoundPrivateNetworkAclEntry = t.add_resource(
        NetworkAclEntry(
            'InboundHTTPNetworkAclEntry',
            NetworkAclId=Ref(networkAcl),
            RuleNumber='100',
            Protocol='6',
            PortRange=PortRange(To='80', From='80'),
            Egress='false',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0',
        ))

    inboundSSHNetworkAclEntry = t.add_resource(
        NetworkAclEntry(
            'InboundSSHNetworkAclEntry',
            NetworkAclId=Ref(networkAcl),
            RuleNumber='101',
            Protocol='6',
            PortRange=PortRange(To='22', From='22'),
            Egress='false',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0',
        ))

    inboundResponsePortsNetworkAclEntry = t.add_resource(
        NetworkAclEntry(
            'InboundResponsePortsNetworkAclEntry',
            NetworkAclId=Ref(networkAcl),
            RuleNumber='102',
            Protocol='6',
            PortRange=PortRange(To='65535', From='1024'),
            Egress='false',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0',
        ))

    outBoundHTTPNetworkAclEntry = t.add_resource(
        NetworkAclEntry(
            'OutBoundHTTPNetworkAclEntry',
            NetworkAclId=Ref(networkAcl),
            RuleNumber='100',
            Protocol='6',
            PortRange=PortRange(To='80', From='80'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0',
        ))

    outBoundHTTPSNetworkAclEntry = t.add_resource(
        NetworkAclEntry(
            'OutBoundHTTPSNetworkAclEntry',
            NetworkAclId=Ref(networkAcl),
            RuleNumber='101',
            Protocol='6',
            PortRange=PortRange(To='443', From='443'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0',
        ))

    outBoundResponsePortsNetworkAclEntry = t.add_resource(
        NetworkAclEntry(
            'OutBoundResponsePortsNetworkAclEntry',
            NetworkAclId=Ref(networkAcl),
            RuleNumber='102',
            Protocol='6',
            PortRange=PortRange(To='65535', From='1024'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0',
        ))

    subnetNetworkAclAssociation = t.add_resource(
        SubnetNetworkAclAssociation(
            'SubnetNetworkAclAssociation',
            SubnetId=subnet_public_id,
            NetworkAclId=Ref(networkAcl),
        ))
    """
    instanceSecurityGroup = t.add_resource(
        SecurityGroup(
            "InstanceSecurityGroup",
            GroupDescription="Enable RDP access via port 3389",
            SecurityGroupIngress=[
                SecurityGroupRule(
                    IpProtocol="tcp",
                    FromPort="3389",
                    ToPort="3389",
                    CidrIp=Ref(sshlocation_param),
                )
            ],
            VpcId=vpc_id,
        )
    )

    """
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:Get*",
                "s3:List*"
            ],
            "Resource": "*"
        }
    ]
}
    """
    slm_iam_role = t.add_resource(
        iam.Role(
            "SLMServerRole",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["ec2.amazonaws.com"]),
                    )
                ]
            ),
            Policies=[
                iam.Policy(
                    PolicyName="SLMServerPolicy",
                    PolicyDocument=Policy(
                        Statement=[
                            Statement(
                                Effect=Allow,
                                Action=[
                                    Action("s3", "List*"),
                                    Action("s3", "Get*"),
                                ],
                                Resource=["arn:aws:s3:::*"],
                            )
                        ]
                    ),
                )
            ],
        )
    )

    slm_instanceprofile = t.add_resource(
        iam.InstanceProfile("SLMServerInstanceProfile", Roles=[Ref(slm_iam_role)])
    )

    # instance_metadata = Metadata()

    instance = t.add_resource(
        Instance(
            "SLMServerInstance",
            # Metadata=instance_metadata,
            ImageId=FindInMap(
                "AWSRegionArch2AMI",
                Ref("AWS::Region"),
                FindInMap("AWSInstanceType2Arch", Ref(instanceType_param), "Arch"),
            ),
            InstanceType=Ref(instanceType_param),
            KeyName=Ref(keyname_param),
            NetworkInterfaces=[
                NetworkInterfaceProperty(
                    NetworkInterfaceId=network_interface_id, DeviceIndex="0"
                )
            ],
            IamInstanceProfile=Ref(slm_instanceprofile),
            UserData=Base64(
                Join(
                    "",
                    [
                        "<powershell>\n",
                        '$ErrorActionPreference = "Stop"\n',
                        "net user Administrator %(password)s\n"
                        % dict(password=ADMIN_PASSWORD),
                        r"Read-S3Object -BucketName %(bucket_name)s -Key SLMLockInfo.zip -File \Users\Administrtor\Desktop\SLMLockInfo.zip\n"
                        % dict(bucket_name=BUCKET_NAME),
                        'Rename-Computer -NewName "SLMServer" -Restart\n'
                        "</powershell>\n",
                    ],
                )
            ),
            Tags=Tags(Name="FOQUS_SLMServer", Application=ref_stack_id),
        )
    )
    """
    ipAddress = t.add_resource(
        EIP('IPAddress',
            DependsOn='AttachGateway',
            Domain='vpc',
            InstanceId=Ref(instance)
            ))
    """

    t.add_output(
        [
            Output(
                "URL",
                Description="Newly created application URL",
                Value=Join("", ["http://", GetAtt("SLMServerInstance", "PublicIp")]),
            )
        ]
    )
    return t


def main():
    cp = ConfigParser()
    cp.read(CONFIG_FILE)
    global BUCKET_NAME, ADMIN_PASSWORD
    BUCKET_NAME = cp.get("S3", "bucket")
    ADMIN_PASSWORD = cp.get("CloudInit", "admin_password")
    op = optparse.OptionParser(
        usage="USAGE: %prog [vpc_id] [subnet_id] [internet_gateway_id] [network_interface_id] [allocation_id]",
        description=main.__doc__,
    )
    (options, args) = op.parse_args()
    # if len(args) != 1: usage()
    # command = args[0]
    # Ref(VPC)
    assert args[0].startswith("vpc-")
    vpc_id = args[0]
    # Ref(subnet_public)
    assert args[1].startswith("subnet-")
    subnet_public_id = args[1]

    ## TODO: ADD THESE TO VPC Main Output
    # Ref(internetGateway)
    assert args[2].startswith("igw-")
    internetgateway_id = args[2]
    assert args[3].startswith("eni-")
    network_interface_id = args[3]
    assert args[4].startswith("eipalloc-")
    allocation_id = args[4]

    t = _create_template(
        vpc_id,
        subnet_public_id,
        internetgateway_id,
        network_interface_id,
        allocation_id,
    )
    print(t.to_json())


if __name__ == "__main__":
    main()
