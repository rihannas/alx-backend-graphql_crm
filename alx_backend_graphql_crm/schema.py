# alx_backend_graphql_crm/schema.py
import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation


class Query(CRMQuery, graphene.ObjectType):
    # Original hello query
    hello = graphene.String()
    
    def resolve_hello(self, info):
        return "Hello, GraphQL!"


class Mutation(CRMMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)