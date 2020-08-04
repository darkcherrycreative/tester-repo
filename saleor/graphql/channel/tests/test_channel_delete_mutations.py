import graphene

from ....channel.error_codes import ChannelErrorCode
from ....checkout.models import Checkout
from ...tests.utils import assert_no_permission, get_graphql_content

CHANNEL_DELETE_MUTATION = """
    mutation deleteChannel($id: ID!,$input: ChannelDeleteInput!){
        channelDelete(id: $id, input: $input){
            channel{
                id
                name
                slug
                currencyCode
            }
            channelErrors{
                field
                code
                message
            }
        }
    }
"""


def test_channel_delete_mutation_as_staff_user(
    order_list,
    checkout,
    permission_manage_channels,
    staff_api_client,
    channel_USD,
    channel_PLN,
    product,
):
    # given
    order = order_list[0]
    order.channel = channel_USD
    order.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_target_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {"id": channel_id, "input": {"targetChannel": channel_target_id}}
    assert Checkout.objects.first() is not None

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_DELETE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    get_graphql_content(response)
    order.refresh_from_db()

    assert order.channel == channel_PLN
    assert Checkout.objects.first() is None


def test_channel_delete_mutation_with_the_same_channel_and_target_channel_id(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {"id": channel_id, "input": {"targetChannel": channel_id}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_DELETE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)
    error = content["data"]["channelDelete"]["channelErrors"][0]

    assert error["field"] == "targetChannel"
    assert error["code"] == ChannelErrorCode.CHANNEL_TARGET_ID_MUST_BE_DIFFERENT.name


def test_channel_delete_mutation_as_app(
    permission_manage_channels,
    app_api_client,
    order_list,
    channel_USD,
    channel_PLN,
    checkout,
):
    # given
    order = order_list[0]
    order.channel = channel_USD
    order.save()
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_target_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {"id": channel_id, "input": {"targetChannel": channel_target_id}}
    assert Checkout.objects.first() is not None

    # when
    response = app_api_client.post_graphql(
        CHANNEL_DELETE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )

    get_graphql_content(response)
    order.refresh_from_db()

    # then
    assert order.channel == channel_PLN
    assert Checkout.objects.first() is None


def test_channel_delete_mutation_as_customer(user_api_client, channel_USD, channel_PLN):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_target_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {"id": channel_id, "input": {"targetChannel": channel_target_id}}

    # when
    response = user_api_client.post_graphql(
        CHANNEL_DELETE_MUTATION, variables=variables, permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_delete_mutation_as_anonymous(api_client, channel_USD, channel_PLN):
    # given
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_target_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    variables = {"id": channel_id, "input": {"targetChannel": channel_target_id}}

    # when
    response = api_client.post_graphql(
        CHANNEL_DELETE_MUTATION, variables=variables, permissions=(),
    )

    # then
    assert_no_permission(response)