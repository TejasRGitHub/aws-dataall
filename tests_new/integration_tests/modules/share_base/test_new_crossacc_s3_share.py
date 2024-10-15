import pytest
from assertpy import assert_that

from tests_new.integration_tests.modules.share_base.conftest import clean_up_share
from tests_new.integration_tests.modules.share_base.queries import (
    create_share_object,
    submit_share_object,
    add_share_item,
    get_share_object,
    reject_share_object,
    delete_share_object,
    update_share_request_reason,
    update_share_reject_reason,
)
from tests_new.integration_tests.modules.share_base.utils import (
    check_share_ready,
)

from tests_new.integration_tests.modules.share_base.shared_test_functions import (
    check_share_items_access,
    check_verify_share_items,
    revoke_and_check_all_shared_items,
    check_all_items_revoke_job_succeeded,
    add_all_items_to_share,
    check_submit_share_object,
    check_approve_share_object,
    check_share_succeeded,
)


def test_create_and_delete_share_object(client5, session_cross_acc_env_1, session_s3_dataset1, principal1, group5):
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(share.status).is_equal_to('Draft')
    delete_share_object(client5, share.shareUri)


def test_submit_empty_object(client5, session_cross_acc_env_1, session_s3_dataset1, group5, principal1):
    # here Exception is not recognized as GqlError, so we use base class
    # toDo: back to GqlError
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    assert_that(submit_share_object).raises(Exception).when_called_with(client5, share.shareUri).contains(
        'ShareItemsFound', 'The request is empty'
    )
    clean_up_share(client5, share.shareUri)


def test_add_share_items(client5, session_cross_acc_env_1, session_s3_dataset1, group5, principal1):
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share = get_share_object(client5, share.shareUri)

    items = share['items'].nodes
    assert_that(len(items)).is_greater_than(0)
    assert_that(items[0].status).is_none()

    item_to_add = items[0]
    share_item_uri = add_share_item(client5, share.shareUri, item_to_add.itemUri, item_to_add.itemType)
    assert_that(share_item_uri).is_not_none()

    updated_share = get_share_object(client5, share.shareUri, {'isShared': True})
    items = updated_share['items'].nodes
    assert_that(items).is_length(1)
    assert_that(items[0].shareItemUri).is_equal_to(share_item_uri)
    assert_that(items[0].status).is_equal_to('PendingApproval')

    clean_up_share(client5, share.shareUri)


def test_reject_share(client1, client5, session_cross_acc_env_1, session_s3_dataset1, group5, principal1):
    principal_id, principal_type = principal1
    share = create_share_object(
        client=client5,
        dataset_or_item_params={'datasetUri': session_s3_dataset1.datasetUri},
        environmentUri=session_cross_acc_env_1.environmentUri,
        groupUri=group5,
        principalId=principal_id,
        principalType=principal_type,
        requestPurpose='test create share object',
        attachMissingPolicies=True,
        permissions=['Read'],
    )
    share = get_share_object(client5, share.shareUri)

    items = share['items'].nodes
    assert_that(len(items)).is_greater_than(0)
    assert_that(items[0].status).is_none()

    item_to_add = items[0]
    add_share_item(client5, share.shareUri, item_to_add.itemUri, item_to_add.itemType)
    submit_share_object(client5, share.shareUri)

    reject_share_object(client1, share.shareUri)
    updated_share = get_share_object(client1, share.shareUri)
    assert_that(updated_share.status).is_equal_to('Rejected')

    change_request_purpose = update_share_reject_reason(client1, share.shareUri, 'new purpose')
    assert_that(change_request_purpose).is_true()
    updated_share = get_share_object(client5, share.shareUri)
    assert_that(updated_share.rejectPurpose).is_equal_to('new purpose')

    clean_up_share(client5, share.shareUri)


def test_change_share_purpose(client5, share_params_main):
    share, dataset = share_params_main
    change_request_purpose = update_share_request_reason(client5, share.shareUri, 'new purpose')
    assert_that(change_request_purpose).is_true()
    updated_share = get_share_object(client5, share.shareUri)
    assert_that(updated_share.requestPurpose).is_equal_to('new purpose')


@pytest.mark.dependency(name='share_submitted')
def test_submit_object(client5, share_params_all):
    share, dataset = share_params_all
    add_all_items_to_share(client5, share.shareUri)
    check_submit_share_object(client5, share.shareUri, dataset)


@pytest.mark.dependency(name='share_approved', depends=['share_submitted'])
def test_approve_share(client1, share_params_main):
    share, dataset = share_params_main
    check_approve_share_object(client1, share.shareUri)


@pytest.mark.dependency(name='share_succeeded', depends=['share_approved'])
def test_share_succeeded(client1, share_params_main):
    share, dataset = share_params_main
    check_share_succeeded(client1, share.shareUri, check_contains_all_item_types=True)


@pytest.mark.dependency(name='share_verified', depends=['share_succeeded'])
def test_verify_share_items(client1, share_params_main):
    share, dataset = share_params_main
    check_verify_share_items(client1, share.shareUri)


@pytest.mark.dependency(depends=['share_verified'])
def test_check_item_access(
    client5, session_cross_acc_env_1_aws_client, share_params_main, group5, session_consumption_role_1
):
    share, dataset = share_params_main
    check_share_items_access(
        client5, group5, share.shareUri, session_consumption_role_1, session_cross_acc_env_1_aws_client
    )


@pytest.mark.dependency(name='share_revoked', depends=['share_succeeded'])
def test_revoke_share(client1, share_params_main):
    share, dataset = share_params_main
    check_share_ready(client1, share.shareUri)
    revoke_and_check_all_shared_items(client1, share.shareUri, check_contains_all_item_types=True)


@pytest.mark.dependency(name='share_revoke_succeeded', depends=['share_revoked'])
def test_revoke_succeeded(
    client1, client5, session_cross_acc_env_1_aws_client, share_params_main, group5, session_consumption_role_1
):
    share, dataset = share_params_main
    check_all_items_revoke_job_succeeded(client1, share.shareUri, check_contains_all_item_types=True)
    check_share_items_access(
        client5, group5, share.shareUri, session_consumption_role_1, session_cross_acc_env_1_aws_client
    )