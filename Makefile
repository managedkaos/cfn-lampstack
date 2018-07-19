AWS=/usr/local/bin/aws
JQ=/usr/local/bin/jq
PROFILE=mmx
DBNAME=miramax
DBUSER=miramax
DBPASS=C0mpl3xPa55w0rd
KEYNAME=dev-stack
STACKNAME=dev-stack

$(STACKNAME).yml: $(STACKNAME).py
	python $< | tee $@

lint: $(STACKNAME).py
	pylint $<

clean:
	@rm $(STACKNAME).yml || echo "All clean! :D"

stack: $(STACKNAME).yml
	@$(AWS) --profile=$(PROFILE) cloudformation create-stack \
		--stack-name $(STACKNAME) \
		--template-body file://$(STACKNAME).yml \
		--tags Key=Name,Value=$(STACKNAME) \
		--parameters ParameterKey=KeyName,ParameterValue=$(KEYNAME) \
		             ParameterKey=DBUser,ParameterValue=$(DBUSER) \
		             ParameterKey=DBName,ParameterValue=$(DBNAME) \
		             ParameterKey=DBPass,ParameterValue=$(DBPASS)
	 $(AWS) --profile=$(PROFILE) cloudformation wait stack-create-complete \
		 --stack-name $(STACKNAME)
	 $(AWS) --profile=$(PROFILE) cloudformation describe-stacks \
		 --stack-name $(STACKNAME) | $(JQ) .Stacks[0].Outputs

describe-stack:
	 $(AWS) --profile=$(PROFILE) cloudformation describe-stacks \
		 --stack-name $(STACKNAME) | $(JQ) .Stacks[0].Outputs

delete-stack:
	$(AWS) --profile=$(PROFILE) cloudformation delete-stack \
		--stack-name $(STACKNAME)
	$(AWS) --profile=$(PROFILE) cloudformation wait stack-delete-complete \
		--stack-name $(STACKNAME)

.PHONY: lint clean stack describe-stack delete-stack
