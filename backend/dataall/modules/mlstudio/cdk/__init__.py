"""
This package contains modules that are used to create a CloudFormation stack in AWS.
The code is invoked in ECS Fargate to initialize the creation of the stack
"""
from dataall.modules.mlstudio.cdk import mlstudio_stack, mlstudio_policy

__all__ = ["mlstudio_stack", "mlstudio_policy"]