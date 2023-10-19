export AWS_REGION=eu-west-1

aws kendra query \
--index-id "3c9a2cd3-b041-4518-a5f4-a688f827b723" \
--attribute-filter '{   
    "EqualsTo":{
      "Key": "_language_code",
      "Value": {
        "StringValue": "nl"
      }
    }
  }' \
--sorting-configuration '{
    "DocumentAttributeKey": "_created_at",
    "SortOrder": "DESC"
  }'