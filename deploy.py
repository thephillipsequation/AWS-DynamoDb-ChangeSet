import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import WaiterError


class cloudformation(object):
    def __init__(self, 
                cfn_string, stackname, 
                table_name="myTable", change_set_name="jp-boto3-changeset" ):
        self.table_name =table_name
        self.change_set_name = change_set_name
        self.client = boto3.client('cloudformation')
        self.cfn_string = cfn_string
        self.stackname = stackname


    def create_change_set(self):
        ''' change_set_type can be UPDATE or CREATE'''
        try:
            change_set = self.client.create_change_set(
                        StackName=self.stackname,
                        TemplateBody=self.cfn_string,
                        Parameters=[
                            {
                                'ParameterKey' : 'dbTableName',
                                'ParameterValue' : self.table_name
                            }
                        ],
                        ChangeSetName=self.change_set_name,
                        ChangeSetType='CREATE'
                        )
            self.wait()
            self.execute_change_set()

        except ClientError as e:
            if e.response['Error']['Code'] == 'ValidationError':
                print "Removing any previously created change sets with the same name"
                self.delete_change_set()                
                print "Create UPDATE change set {}".format(self.change_set_name)
                change_set = self.client.create_change_set(
                        StackName=self.stackname,
                        TemplateBody=self.cfn_string,
                        Parameters=[
                            {
                                'ParameterKey' : 'dbTableName',
                                'ParameterValue' : self.table_name
                            }
                        ],
                        ChangeSetName=self.change_set_name,
                        ChangeSetType='UPDATE'
                        )
                self.wait()
                print type(self.get_change_status())
                if self.get_change_status() is not 'True':
                    raise Exception("Change Set Cannot be excuted as the table would be replaced")
                else:
                    self.execute_change_set()
            else:
                print "Unexpected error: {}".format(e)

    def wait(self):
        print "Waiting for change set create complete"
        waiter = self.client.get_waiter('change_set_create_complete')
        try:
            waiter.wait(
                ChangeSetName=self.change_set_name,
                StackName=self.stackname,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts' : 120
                }
            )
            print "Change Set Complete"
        except WaiterError:
            raise Exception("Your Change Set Does not Contain Any Changes")
            


    def delete_change_set(self):
        self.client.delete_change_set(
            ChangeSetName=self.change_set_name,
            StackName=self.stackname
        )
            
    def get_change_status(self):
        describe_response = self.client.describe_change_set(
            ChangeSetName=self.change_set_name,
            StackName=self.stackname
        )

        # Boolean value for the modify action if replacement is true than the resource is deleted and recreated
        #print describe_response["Changes"][0]["ResourceChange"]["Replacement"]
        return describe_response["Changes"][0]["ResourceChange"]["Replacement"]

    def execute_change_set(self):
        print "Executing change set {} on stack {}".format(self.change_set_name, self.stackname)
        self.client.execute_change_set(
            ChangeSetName=self.change_set_name,
            StackName=self.stackname
            )

def main():
    with open('dynamodb.yml') as f:
        template_string = f.read()

    cf1 = cloudformation( cfn_string=template_string, 
                         stackname='jp-test-1', 
                         table_name="myTableName", 
                         change_set_name="change-set-1")
    cf1.create_change_set()

if __name__ == "__main__":
    main()

