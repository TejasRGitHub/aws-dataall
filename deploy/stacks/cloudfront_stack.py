from builtins import super

from aws_cdk import Stack
from .cloudfront import CloudfrontDistro
from .frontend_cognito_config import FrontendCognitoConfig
from .auth_at_edge import AuthAtEdge


class CloudfrontStack(Stack):
    def __init__(
        self,
        scope,
        id,
        envname: str = 'dev',
        resource_prefix='dataall',
        tooling_account_id=None,
        custom_domain=None,
        custom_waf_rules=None,
        custom_auth=None,
        backend_region=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        auth_at_edge = (
            AuthAtEdge(
                self,
                'AuthAtEdge',
                envname=envname,
                resource_prefix=resource_prefix,
                **kwargs,
            )
            if custom_auth is None
            else None
        )

        distro = CloudfrontDistro(
            self,
            'CloudFront',
            envname=envname,
            resource_prefix=resource_prefix,
            auth_at_edge=auth_at_edge,
            tooling_account_id=tooling_account_id,
            custom_domain=custom_domain,
            custom_waf_rules=custom_waf_rules,
            custom_auth=custom_auth,
            backend_region=backend_region,
            **kwargs,
        )

        if not custom_auth:
            FrontendCognitoConfig(
                self,
                'FrontendCognitoConfig',
                envname=envname,
                resource_prefix=resource_prefix,
                custom_domain=custom_domain,
                backend_region=backend_region,
                execute_after=[distro],
                **kwargs,
            )
