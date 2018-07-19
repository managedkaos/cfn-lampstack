'''Module: Make an EC2 Instance'''
import time
import troposphere.ec2 as ec2
from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Parameter, Output, Ref, Template
from troposphere.cloudformation import Init, InitConfig, InitFiles, InitFile, Metadata
from troposphere.policies import CreationPolicy, ResourceSignal
from create_ami_region_map import create_ami_region_map

def main():
    '''Function: Generates the Cloudformation template'''
    template = Template()

    keyname_param = template.add_parameter(
        Parameter(
            'KeyName',
            Description='An existing EC2 KeyPair.',
            ConstraintDescription='An existing EC2 KeyPair.',
            Type='AWS::EC2::KeyPair::KeyName',
        )
    )

    _param = template.add_parameter(
        Parameter(
            '',
            Type='String',
            Description='',
            ConstraintDescription='',
            AllowedPattern="[-_a-zA-Z0-9]*",
        )
    )


    template.add_mapping('RegionMap', create_ami_region_map())

    print(template.to_yaml())

if __name__ == '__main__':
    main()
