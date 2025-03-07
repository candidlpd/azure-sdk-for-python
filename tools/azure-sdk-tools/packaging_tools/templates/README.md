# Microsoft Azure SDK for Python

This is the Microsoft Azure {{package_pprint_name}} Client Library.
This package has been tested with Python 3.7+.
For a more complete view of Azure libraries, see the [azure sdk python release](https://aka.ms/azsdk/python/all).

## _Disclaimer_

_Azure SDK Python packages support for Python 2.7 has ended 01 January 2022. For more information and questions, please refer to https://github.com/Azure/azure-sdk-for-python/issues/20691_

# Usage

{% if is_arm %}
To learn how to use this package, see the [quickstart guide](https://aka.ms/azsdk/python/mgmt)
{% endif %}

{%- if not sample_link -%}
{%- set sample_link="https://aka.ms/azsdk/python/mgmt/samples" -%}
{%- else -%}
{%- set sample_link="https://github.com/Azure-Samples/azure-samples-python-management/tree/main/samples/" + sample_link -%}
{%- endif -%}

{% if is_arm %} 
For docs and references, see [Python SDK References](https://docs.microsoft.com/python/api/overview/azure/{{package_doc_id}})
Code samples for this package can be found at [{{package_pprint_name}}](https://docs.microsoft.com/samples/browse/?languages=python&term=Getting%20started%20-%20Managing&terms=Getting%20started%20-%20Managing) on docs.microsoft.com.
Additional code samples for different Azure services are available at [Samples Repo]({{ sample_link }})
{% else %}
For code examples, see [{{package_pprint_name}}](https://docs.microsoft.com/python/api/overview/azure/{{package_doc_id}}) on docs.microsoft.com.
{% endif %}

# Provide Feedback

If you encounter any bugs or have suggestions, please file an issue in the
[Issues](https://github.com/Azure/azure-sdk-for-python/issues)
section of the project. 


![Impressions](https://azure-sdk-impressions.azurewebsites.net/api/impressions/azure-sdk-for-python%2F{{package_name}}%2FREADME.png)
