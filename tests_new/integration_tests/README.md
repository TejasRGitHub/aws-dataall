# Integration tests

The purpose of these tests is to automatically validate functionalities of data.all on a real deployment.

🚨🚨🚨

Currently **we support only Cognito based deployments** but support for any IdP is on the plans

🚨🚨🚨

## Pre-requisites

- A real deployment of data.all in AWS
- An SSM parameter (`/{resource_prefix/{env_name}/testdata`) with the following contents
    ```
    {
      "users": {
        "testUserTenant": {
          "username": "testUserTenant",
          "password": "...",
          "groups": [
            "DAAdministrators"
          ]
        },
        "testUser1": {
          "username": "testUser1",
          "password": "...",
          "groups": [
            "testGroup1"
          ]
        },
        "testUser2": {
          "username": "testUser2",
          "password": "...",
          "groups": [
            "testGroup2"
          ]
        },
        "testUser3": {
          "username": "testUser3",
          "password": "...",
          "groups": [
            "testGroup3"
          ]
        },
        "testUser4": {
          "username": "testUser4",
          "password": "...",
          "groups": [
            "testGroup4"
          ]
        }
      },
      "envs": {
        "session_env1": {
          "accountId": "...",
          "region": "eu-central-1"
        },
        "session_env2": {
          "accountId": "...",
          "region": "eu-west-1"
        }
      }
    }
    ```
- The pipeline will create the users/groups

## Run tests

The tests are executed in CodeBuild as part of the CICD pipeline if the cdk.json parameter `with_approval_tests` is set
to True.

You can also run the tests locally by...

* Authenticating to your data.all environment account (you might want to set the `AWS_PROFILE` env variable)

* ```bash
  export ENVNAME = "Introduce deployment environment name"
  export AWS_REGION = "Introduce backend region"
  export COGNITO_CLIENT = "Introduce Cognito client id"
  export API_ENDPOINT = "Introduce API endpoint url"
  echo "add your testdata here" > testdata.json 
  make integration-tests
  ```

## Coverage

At the moment integration tests only cover Organizations module as an example.