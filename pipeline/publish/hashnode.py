"""Hashnode publisher via GraphQL API.

Auth: Personal Access Token header. Endpoint: POST https://gql.hashnode.com.
Two-step: createDraft -> publishDraft.
Rate limit: 500 mutations/min.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from pipeline.config import Config
from pipeline.publish import PostResult

HASHNODE_GQL_URL = "https://gql.hashnode.com"

CREATE_DRAFT_MUTATION = """
mutation CreateDraft($input: CreateDraftInput!) {
  createDraft(input: $input) {
    draft {
      id
      slug
    }
  }
}
"""

PUBLISH_DRAFT_MUTATION = """
mutation PublishDraft($input: PublishDraftInput!) {
  publishDraft(input: $input) {
    post {
      id
      slug
      url
    }
  }
}
"""


@dataclass
class HashnodePublisher:
    channel: str = "hashnode"

    def publish(
        self,
        draft: str,
        config: Config,
        title: str | None = None,
        tags: list[str] | None = None,
        canonical_url: str | None = None,
    ) -> PostResult:
        creds = config.require_hashnode()

        if config.dry_run:
            return PostResult(
                url=None,
                channel=self.channel,
                success=True,
                error="[dry run] would post to Hashnode",
            )

        if title is None:
            first_line = draft.strip().split("\n", 1)[0]
            if first_line.startswith("# "):
                title = first_line.lstrip("# ").strip()
                draft = draft.strip().split("\n", 1)[1].strip() if "\n" in draft.strip() else draft
            else:
                sentence = first_line.split(". ")[0].split(" — ")[0]
                title = sentence[:70].rstrip(" .,")


        headers = {
            "Authorization": creds.pat,
            "Content-Type": "application/json",
        }

        try:
            # Step 1: Create draft
            draft_input: dict = {
                "publicationId": creds.publication_id,
                "title": title,
                "contentMarkdown": draft,
            }
            if canonical_url:
                draft_input["originalArticleURL"] = canonical_url

            resp = httpx.post(
                HASHNODE_GQL_URL,
                json={"query": CREATE_DRAFT_MUTATION, "variables": {"input": draft_input}},
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            if "errors" in data:
                return PostResult(
                    url=None,
                    channel=self.channel,
                    success=False,
                    error=f"GraphQL errors: {data['errors']}",
                )

            draft_id = data["data"]["createDraft"]["draft"]["id"]

            # Step 2: Publish draft
            resp = httpx.post(
                HASHNODE_GQL_URL,
                json={
                    "query": PUBLISH_DRAFT_MUTATION,
                    "variables": {"input": {"draftId": draft_id}},
                },
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            if "errors" in data:
                return PostResult(
                    url=None,
                    channel=self.channel,
                    success=False,
                    error=f"GraphQL errors: {data['errors']}",
                )

            post_url = data["data"]["publishDraft"]["post"]["url"]
            return PostResult(url=post_url, channel=self.channel, success=True)

        except Exception as e:
            return PostResult(
                url=None,
                channel=self.channel,
                success=False,
                error=str(e),
            )
