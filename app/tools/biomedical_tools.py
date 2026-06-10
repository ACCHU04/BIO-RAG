"""
Biomedical external API tools for the agentic pipeline.
Covers PubMed (literature), UniProt (proteins), Open Targets (drug-gene-disease).
"""

import requests
from typing import List, Dict, Any, Optional
from Bio import Entrez
from loguru import logger

from app.config import get_settings

settings = get_settings()
Entrez.email = settings.entrez_email
if settings.entrez_api_key:
    Entrez.api_key = settings.entrez_api_key


# ── PubMed ────────────────────────────────────────────────────────────────────

def search_pubmed(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search PubMed for biomedical literature.
    Returns list of article summaries with title, abstract, authors, year.
    """
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()

        ids = record["IdList"]
        if not ids:
            return []

        handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        articles = []
        for article in records["PubmedArticle"]:
            medline = article["MedlineCitation"]
            art = medline["Article"]

            title = str(art.get("ArticleTitle", "No title"))
            abstract = ""
            if "Abstract" in art:
                abstract_texts = art["Abstract"].get("AbstractText", [])
                if isinstance(abstract_texts, list):
                    abstract = " ".join(str(t) for t in abstract_texts)
                else:
                    abstract = str(abstract_texts)

            authors = []
            if "AuthorList" in art:
                for author in art["AuthorList"][:3]:
                    name = author.get("LastName", "") + " " + author.get("ForeName", "")
                    authors.append(name.strip())

            year = ""
            pub_date = art.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            year = str(pub_date.get("Year", pub_date.get("MedlineDate", "")))

            pmid = str(medline["PMID"])
            articles.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract[:800],
                "authors": authors,
                "year": year,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

        logger.info(f"PubMed returned {len(articles)} articles for: '{query}'")
        return articles

    except Exception as e:
        logger.error(f"PubMed search failed: {e}")
        return []


# ── UniProt ───────────────────────────────────────────────────────────────────

def search_uniprot(gene_name: str, organism: str = "human") -> List[Dict[str, Any]]:
    """
    Search UniProt for protein information related to a gene.
    Returns protein name, function, associated diseases, and GO terms.
    """
    try:
        url = "https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": f"gene:{gene_name} AND organism_name:{organism} AND reviewed:true",
            "fields": "accession,gene_names,protein_name,organism_name,cc_function,cc_disease,go",
            "format": "json",
            "size": 3,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for entry in data.get("results", []):
            protein_name = entry.get("proteinDescription", {}).get(
                "recommendedName", {}
            ).get("fullName", {}).get("value", "Unknown")

            functions = []
            for comment in entry.get("comments", []):
                if comment.get("commentType") == "FUNCTION":
                    for text in comment.get("texts", []):
                        functions.append(text.get("value", "")[:300])

            diseases = []
            for comment in entry.get("comments", []):
                if comment.get("commentType") == "DISEASE":
                    disease = comment.get("disease", {})
                    diseases.append(disease.get("diseaseId", ""))

            results.append({
                "accession": entry.get("primaryAccession", ""),
                "protein_name": protein_name,
                "gene": gene_name,
                "organism": organism,
                "functions": functions[:2],
                "associated_diseases": diseases[:5],
            })

        logger.info(f"UniProt returned {len(results)} entries for gene: {gene_name}")
        return results

    except Exception as e:
        logger.error(f"UniProt search failed: {e}")
        return []


# ── Open Targets ──────────────────────────────────────────────────────────────

def search_open_targets(disease_name: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Query Open Targets GraphQL API for drug-gene-disease associations.
    Returns top target genes and drugs associated with a disease.
    """
    try:
        url = "https://api.platform.opentargets.org/api/v4/graphql"
        query = """
        query DiseaseTargets($disease: String!, $size: Int!) {
          search(queryString: $disease, entityNames: ["disease"]) {
            hits {
              id
              name
              object {
                ... on Disease {
                  id
                  name
                  associatedTargets(page: {index: 0, size: $size}) {
                    rows {
                      target {
                        approvedSymbol
                        approvedName
                      }
                      score
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {"disease": disease_name, "size": max_results}
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("data", {}).get("search", {}).get("hits", [])
        results = []

        for hit in hits[:1]:
            obj = hit.get("object", {})
            assoc_targets = obj.get("associatedTargets", {}).get("rows", [])
            for row in assoc_targets:
                target = row.get("target", {})
                results.append({
                    "disease": disease_name,
                    "gene_symbol": target.get("approvedSymbol", ""),
                    "gene_name": target.get("approvedName", ""),
                    "association_score": round(row.get("score", 0), 4),
                })

        logger.info(f"Open Targets returned {len(results)} associations for: {disease_name}")
        return results

    except Exception as e:
        logger.error(f"Open Targets search failed: {e}")
        return []
