'''Module: Make an EC2 Instance'''
import time
import troposphere.ec2 as ec2
from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Parameter, Output, Ref, Template
from troposphere.rds import DBInstance
from troposphere.cloudformation import Init, InitConfig, InitFiles, InitFile, Metadata
from troposphere.policies import CreationPolicy, ResourceSignal

def main():
    '''Function: Generates the Cloudformation template'''
    template = Template()
    template.add_description("Dev Stack")

    keyname_param = template.add_parameter(
        Parameter(
            'KeyName',
            Description='An existing EC2 KeyPair.',
            ConstraintDescription='An existing EC2 KeyPair.',
            Type='AWS::EC2::KeyPair::KeyName',
        )
    )

    db_pass_param = template.add_parameter(
        Parameter(
            'DBPass',
            NoEcho=True,
            Type='String',
            Description='The database admin account password',
            ConstraintDescription='Must contain only alphanumeric characters',
            AllowedPattern="[-_a-zA-Z0-9]*",
        )
    )

    db_name_param = template.add_parameter(
        Parameter(
            'DBName',
            Default='miramax',
            Type='String',
            Description='The database name',
            ConstraintDescription='Must begin with a letter and contain only alphanumeric characters',
            AllowedPattern="[-_a-zA-Z0-9]*",
        )
    )

    db_user_param = template.add_parameter(
        Parameter(
            'DBUser',
            Default='miramax',
            Type='String',
            Description='Username for MySQL database access',
            ConstraintDescription='Must begin with a letter and contain only alphanumeric characters',
            AllowedPattern="[-_a-zA-Z0-9]*",
        )
    )

    template.add_mapping('RegionMap', {'ap-south-1': {'ami': 'ami-ee8ea481'}, 'eu-west-3': {'ami': 'ami-daf040a7'}, 'eu-west-2': {'ami': 'ami-ddb950ba'}, 'eu-west-1': {'ami': 'ami-d2414e38'}, 'ap-northeast-2': {'ami': 'ami-65d86d0b'}, 'ap-northeast-1': {'ami': 'ami-e875a197'}, 'sa-east-1': {'ami': 'ami-ccd48ea0'}, 'ca-central-1': {'ami': 'ami-c3e567a7'}, 'ap-southeast-1': {'ami': 'ami-31e7e44d'}, 'ap-southeast-2': {'ami': 'ami-23c51c41'}, 'eu-central-1': {'ami': 'ami-3c635cd7'}, 'us-east-1': {'ami': 'ami-5cc39523'}, 'us-east-2': {'ami': 'ami-67142d02'}, 'us-west-1': {'ami': 'ami-d7b355b4'}, 'us-west-2': {'ami': 'ami-39c28c41'}})

    ec2_security_group = template.add_resource(
        ec2.SecurityGroup(
            'EC2SecurityGroup',
            Tags=[{'Key':'Name', 'Value':Ref('AWS::StackName')},],
            GroupDescription='EC2 Security Group',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='22',
                    ToPort='22',
                    CidrIp='0.0.0.0/0',
                    Description='SSH'),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='80',
                    ToPort='80',
                    CidrIp='0.0.0.0/0',
                    Description='HTTP'),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='443',
                    ToPort='443',
                    CidrIp='0.0.0.0/0',
                    Description='HTTPS'),
            ],
        )
    )

    db_security_group = template.add_resource(
        ec2.SecurityGroup(
            'DBSecurityGroup',
            Tags=[{'Key':'Name', 'Value':Ref('AWS::StackName')},],
            GroupDescription='DB Security Group',
            SecurityGroupIngress=[
                    ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort='3306',
                    ToPort='3306',
                    SourceSecurityGroupId=GetAtt(ec2_security_group, "GroupId"),
                    Description='MySQL'),
            ]
        )
    )
    ec2_instance = template.add_resource(
        ec2.Instance(
            'Instance',
            Metadata=Metadata(
                Init({
                    "config": InitConfig(
                        files=InitFiles({
                            "/tmp/instance.txt": InitFile(
                                content=Ref('AWS::StackName'),
                                mode="000644",
                                owner="root",
                                group="root"
                            )
                        }),
                    )
                }),
            ),
            CreationPolicy=CreationPolicy(
                ResourceSignal=ResourceSignal(Timeout='PT15M')
            ),
            Tags=[{'Key':'Name', 'Value':Ref('AWS::StackName')},],
            ImageId=FindInMap('RegionMap', Ref('AWS::Region'), 'ami'),
            InstanceType='t2.micro',
            KeyName=Ref(keyname_param),
            SecurityGroups=[Ref(ec2_security_group), Ref(db_security_group)],
            DependsOn='Database',
            UserData=Base64(
                Join(
                    '',
                    [
                        '#!/bin/bash -x\n',
                        'exec > /tmp/user-data.log 2>&1\n',
                        'unset UCF_FORCE_CONFFOLD\n',
                        'export UCF_FORCE_CONFFNEW=YES\n',
                        'ucf --purge /boot/grub/menu.lst\n',
                        'export DEBIAN_FRONTEND=noninteractive\n',
                        'apt-get update\n',
                        'apt-get -o Dpkg::Options::="--force-confnew" --force-yes -fuy upgrade\n',
			'apt-get install -y python-pip apache2 libapache2-mod-wsgi\n',
			'pip install https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz\n',
                        '# Signal Cloudformation when set up is complete\n',
                        '/usr/local/bin/cfn-signal -e $? --resource=Instance --region=', Ref('AWS::Region'), ' --stack=', Ref('AWS::StackName'), '\n',
                    ]
                )
            )
        )
    )

    ip_association = template.add_resource(
        ec2.EIPAssociation(
            'IPAssociation',
            InstanceId=Ref(ec2_instance),
            AllocationId='eipalloc-aa755d96'
        )
    )

    db_instance = template.add_resource(
        DBInstance(
            'Database',
            DBName=Ref(db_name_param),
            AllocatedStorage=20,
            DBInstanceClass='db.t2.micro',
            Engine='MySQL',
            EngineVersion='5.7.21',
            MasterUsername=Ref(db_user_param),
            MasterUserPassword=Ref(db_pass_param),
            VPCSecurityGroups=[GetAtt(db_security_group, "GroupId")],
        )
    )

    template.add_output([
        Output(
            'InstanceDnsName',
            Description='PublicDnsName',
            Value=GetAtt(ec2_instance, 'PublicDnsName'),
        ),
        Output(
            'DatabaseDnsName',
            Description='DBEndpoint',
            Value=GetAtt(db_instance, 'Endpoint.Address'),
        ),
    ])

    print(template.to_yaml())

if __name__ == '__main__':
    main()
