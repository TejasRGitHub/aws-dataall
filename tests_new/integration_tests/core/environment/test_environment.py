import logging
from datetime import datetime

from assertpy import assert_that

from integration_tests.core.environment.queries import (
    get_environment,
    update_environment,
    list_environments,
    invite_group_on_env,
    add_consumption_role,
    remove_consumption_role,
    remove_group_from_env,
)
from integration_tests.core.stack.queries import update_stack
from integration_tests.core.stack.utils import check_stack_in_progress, check_stack_ready
from integration_tests.errors import GqlError

log = logging.getLogger(__name__)


def test_create_env(session_env1):
    assert_that(session_env1.stack.status).is_in('CREATE_COMPLETE', 'UPDATE_COMPLETE')


def test_modify_env(client1, session_env1):
    test_description = f'a test description {datetime.utcnow().isoformat()}'
    env_uri = session_env1.environmentUri
    updated_env = update_environment(client1, env_uri, {'description': test_description})
    assert_that(updated_env).contains_entry(environmentUri=env_uri, description=test_description)
    env = get_environment(client1, env_uri)
    assert_that(env).contains_entry(environmentUri=env_uri, description=test_description)


def test_modify_env_unauthorized(client1, client2, session_env1):
    test_description = f'unauthorized {datetime.utcnow().isoformat()}'
    env_uri = session_env1.environmentUri
    assert_that(update_environment).raises(GqlError).when_called_with(
        client2, env_uri, {'description': test_description}
    ).contains('UnauthorizedOperation', env_uri)
    env = get_environment(client1, env_uri)
    assert_that(env).contains_entry(environmentUri=env_uri).does_not_contain_entry(description=test_description)


def test_list_envs_authorized(client1, session_env1, session_env2, session_id):
    assert_that(list_environments(client1, term=session_id).nodes).is_length(2)


def test_list_envs_invited(client2, session_env1, session_env2, session_id):
    assert_that(list_environments(client2, term=session_id).nodes).is_length(1)


def test_persistent_env_update(client1, persistent_env1):
    # wait for stack to get to a final state before triggering an update
    stack_uri = persistent_env1.stack.stackUri
    env_uri = persistent_env1.environmentUri
    check_stack_ready(client1, env_uri, stack_uri)
    update_stack(client1, env_uri, 'environment')
    # wait for stack to move to "in_progress" state
    check_stack_in_progress(client1, env_uri, stack_uri)
    stack = check_stack_ready(client1, env_uri, stack_uri)
    assert_that(stack.status).is_equal_to('UPDATE_COMPLETE')


def test_invite_group_on_env_no_org(client1, session_env2, group4):
    assert_that(invite_group_on_env).raises(GqlError).when_called_with(
        client1, session_env2.environmentUri, group4, ['CREATE_DATASET']
    ).contains(group4, 'is not a member of the organization')


def test_invite_group_on_env_unauthorized(client2, session_env2, group2):
    assert_that(invite_group_on_env).raises(GqlError).when_called_with(
        client2, session_env2.environmentUri, group2, ['CREATE_DATASET']
    ).contains('UnauthorizedOperation', 'INVITE_ENVIRONMENT_GROUP', session_env2.environmentUri)


def test_invite_group_on_env(client1, client2, session_env2, group2):
    env_uri = session_env2.environmentUri
    assert_that(list_environments(client2).nodes).extracting('environmentUri').contains(env_uri)
    # assert that client2 can get the environment
    assert_that(get_environment(client2, env_uri)).contains_entry(userRoleInEnvironment='Invited')


def test_invite_remove_group_on_env(client1, client3, session_env2, group3):
    env_uri = session_env2.environmentUri
    try:
        assert_that(list_environments(client3).nodes).extracting('environmentUri').does_not_contain(env_uri)
        assert_that(invite_group_on_env(client1, env_uri, group3, ['CREATE_DATASET'])).contains_entry(
            environmentUri=env_uri
        )
        # assert that client3 can get the environment
        assert_that(get_environment(client3, env_uri)).contains_entry(userRoleInEnvironment='Invited')
    finally:
        assert_that(remove_group_from_env(client1, env_uri, group3)).contains_entry(environmentUri=env_uri)
        assert_that(get_environment).raises(GqlError).when_called_with(client3, env_uri).contains(
            'UnauthorizedOperation', 'GET_ENVIRONMENT', env_uri
        )


def test_add_remove_consumption_role(client1, session_env2, group1):
    env_uri = session_env2.environmentUri
    consumption_role = None
    try:
        consumption_role = add_consumption_role(
            client1, env_uri, group1, 'TestConsumptionRole', f'arn:aws:iam::{session_env2.AwsAccountId}:role/Admin'
        )
        assert_that(consumption_role).contains_key(
            'consumptionRoleUri', 'consumptionRoleName', 'environmentUri', 'groupUri', 'IAMRoleArn'
        )
    finally:
        if consumption_role:
            assert_that(remove_consumption_role(client1, env_uri, consumption_role.consumptionRoleUri)).is_true()


def test_add_consumption_role_unauthorized(client2, session_env2, group1):
    env_uri = session_env2.environmentUri
    assert_that(add_consumption_role).raises(GqlError).when_called_with(
        client2, env_uri, group1, 'TestConsumptionRole', f'arn:aws:iam::{session_env2.AwsAccountId}:role/Admin'
    ).contains('UnauthorizedOperation', 'ADD_ENVIRONMENT_CONSUMPTION_ROLES', env_uri)
