from beanie.odm.queries.find import FindMany
from beanie import Document
from typing import Any
from pymongo.asynchronous.client_session import AsyncClientSession

class CustomFindMany(FindMany):

    async def distinct(
        self,
        key: Any,
        session: AsyncClientSession | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        if self.fetch_links:
            aggregation_pipeline = [
                *(
                    stage
                    for stage in self.build_aggregation_pipeline()
                    if "$sort" not in stage
                    and "$skip" not in stage
                    and "$limit" not in stage
                ),
                {
                    "$unwind": {
                        "path": f"${key}",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
                {
                    "$set": {
                        key: {
                            "$arrayToObject": {
                                "$filter": {
                                    "input": {"$objectToArray": f"${key}"},
                                    "as": "field",
                                    "cond": {"$ne": ["$$field.k", "_id"]},
                                }
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "distinct": {"$addToSet": f"${key}"},
                    }
                },
                {
                    "$set": {
                        "distinct": {
                            "$sortArray": {
                                "input": "$distinct",
                                "sortBy": {"number": 1}
                            }
                        }
                    }
                }
            ]

            kwargs = {**self.pymongo_kwargs, **kwargs}

            cursor = await self.document_model.get_pymongo_collection().aggregate(
                aggregation_pipeline,
                session=session or self.session,
                **kwargs,
            )

            result = await cursor.to_list(length=1)
            return result[0]["distinct"] if result else []

        kwargs = {**self.pymongo_kwargs, **kwargs}

        return await self.document_model.get_pymongo_collection().distinct(
            key=key,
            filter=self.get_filter_query(),
            session=session or self.session,
            **kwargs,
        )

class CustomDocument(Document):
    _find_many_query_class = CustomFindMany