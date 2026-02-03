import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from requests.auth import HTTPBasicAuth


class DataForSEOScraper:
    def __init__(self, login: str, password: str, output_dir: Optional[str] = None):
        if not login or not password:
            raise ValueError("Missing DataForSEO credentials")
        self.base_url = "https://api.dataforseo.com"
        self.auth = HTTPBasicAuth(login, password)

        if output_dir:
            self.output_dir = output_dir
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
            self.output_dir = os.path.join(project_root, "dataforseo_scraper_output")

    # ========================================
    # Public API
    # ========================================
    def run(
        self,
        keywords: List[str],
        max_expand_depth: int = 1,
        location_code: int = 2616,
        language_code: str = "pl",
        device: str = "desktop",
        os_name: str = "windows",
        serp_depth: int = 100,
    ) -> Dict[str, Any]:
        start_time = time.time()
        seeds = self._normalize_keywords(keywords)
        if not seeds:
            raise ValueError("No valid keywords provided")

        keyword_sources: Dict[str, Set[str]] = {}
        for seed in seeds:
            self._add_source(keyword_sources, seed, "seed")

        queue: List[Tuple[str, int]] = [(k, 0) for k in seeds]
        seen: Set[str] = set()
        results: Dict[str, Any] = {}
        errors: List[Dict[str, Any]] = []

        while queue:
            keyword, depth = queue.pop(0)
            if keyword in seen:
                continue
            seen.add(keyword)

            serp_data = {
                "organic": [],
                "people_also_ask": [],
                "people_also_search": [],
                "related_searches": [],
                "ai_overview": None,
                "raw_item_types": []
            }
            autocomplete_items: List[str] = []

            try:
                serp_result = self._fetch_serp(
                    keyword=keyword,
                    location_code=location_code,
                    language_code=language_code,
                    device=device,
                    os_name=os_name,
                    depth=serp_depth
                )
                serp_data = self._parse_serp(serp_result)
            except Exception as e:
                errors.append({"keyword": keyword, "stage": "serp", "error": str(e)})

            try:
                autocomplete_result = self._fetch_autocomplete(
                    keyword=keyword,
                    location_code=location_code,
                    language_code=language_code
                )
                autocomplete_items = self._parse_autocomplete(autocomplete_result)
            except Exception as e:
                errors.append({"keyword": keyword, "stage": "autocomplete", "error": str(e)})

            # Expansion sources
            for kw in serp_data.get("related_searches", []):
                self._add_source(keyword_sources, kw, "related_searches")
            for kw in serp_data.get("people_also_search", []):
                self._add_source(keyword_sources, kw, "people_also_search")
            for kw in autocomplete_items:
                self._add_source(keyword_sources, kw, "autocomplete")

            if depth < max_expand_depth:
                for kw in serp_data.get("related_searches", []):
                    nk = self._normalize_keyword(kw)
                    if nk and nk not in seen:
                        queue.append((nk, depth + 1))
                for kw in serp_data.get("people_also_search", []):
                    nk = self._normalize_keyword(kw)
                    if nk and nk not in seen:
                        queue.append((nk, depth + 1))
                for kw in autocomplete_items:
                    nk = self._normalize_keyword(kw)
                    if nk and nk not in seen:
                        queue.append((nk, depth + 1))

            results[keyword] = {
                "keyword": keyword,
                "sources": sorted(list(keyword_sources.get(keyword, set()))),
                "serp": serp_data,
                "autocomplete": autocomplete_items,
            }

        # Search volume for all collected keywords
        search_volume_data: Dict[str, Any] = {}
        try:
            search_volume_data = self._fetch_search_volume(
                keywords=list(seen),
                location_code=location_code,
                language_code=language_code
            )
        except Exception as e:
            errors.append({"keyword": "__all__", "stage": "search_volume", "error": str(e)})

        # Attach search volume per keyword
        for kw in results.keys():
            results[kw]["search_volume"] = search_volume_data.get(kw)

        run_id = uuid.uuid4().hex
        output = {
            "run_id": run_id,
            "seed_keywords": seeds,
            "config": {
                "max_expand_depth": max_expand_depth,
                "location_code": location_code,
                "language_code": language_code,
                "device": device,
                "os": os_name,
                "serp_depth": serp_depth
            },
            "stats": {
                "total_keywords": len(seen),
                "processed_keywords": len(results),
                "errors": len(errors),
                "duration_seconds": round(time.time() - start_time, 2)
            },
            "keywords": results,
            "errors": errors
        }

        self._write_outputs(run_id, output)
        return output

    # ========================================
    # DataForSEO API
    # ========================================
    def _request(self, method: str, path: str, payload: Optional[Any] = None, timeout: int = 60) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if method == "POST":
            response = requests.post(url, auth=self.auth, json=payload, timeout=timeout)
        else:
            response = requests.get(url, auth=self.auth, timeout=timeout)
        if response.status_code != 200:
            raise RuntimeError(f"DataForSEO HTTP {response.status_code}: {response.text}")
        return response.json()

    def _task_post(self, path: str, payload: Any) -> str:
        data = self._request("POST", path, payload=payload, timeout=60)
        task = self._first_task(data)
        error = self._task_error(task)
        if error:
            raise RuntimeError(error)
        task_id = task.get("id")
        if not task_id:
            raise RuntimeError("DataForSEO task_post did not return task_id")
        return task_id

    def _task_get(self, path: str, task_id: str, max_wait: int = 90, poll_interval: int = 2) -> Dict[str, Any]:
        deadline = time.time() + max_wait
        while time.time() < deadline:
            data = self._request("GET", f"{path.rstrip('/')}/{task_id}", timeout=60)
            task = self._first_task(data)
            status_code = task.get("status_code")
            if status_code == 20000:
                return task
            if status_code in (20100, 20101, 20102):
                time.sleep(poll_interval)
                continue
            error = self._task_error(task) or f"Unexpected status_code={status_code}"
            raise RuntimeError(error)
        raise RuntimeError("DataForSEO task timeout")

    # ========================================
    # SERP
    # ========================================
    def _fetch_serp(self, keyword: str, location_code: int, language_code: str, device: str, os_name: str, depth: int) -> Dict[str, Any]:
        payload = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "device": device,
            "os": os_name,
            "depth": depth
        }]
        task_id = self._task_post("v3/serp/google/organic/task_post", payload)
        task = self._task_get("v3/serp/google/organic/task_get/advanced", task_id, max_wait=120, poll_interval=3)
        result = (task.get("result") or [])
        if not result:
            raise RuntimeError("No SERP result returned")
        return result[0]

    def _parse_serp(self, result: Dict[str, Any]) -> Dict[str, Any]:
        organic: List[Dict[str, Any]] = []
        paa: List[Dict[str, Any]] = []
        related_searches: List[str] = []
        people_also_search: List[str] = []
        ai_overview: Optional[Dict[str, Any]] = None

        items = result.get("items", []) or []
        item_types = result.get("item_types", []) or []

        for item in items:
            item_type = item.get("type")

            if item_type == "organic":
                organic.append({
                    "rank": item.get("rank_absolute"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "domain": item.get("domain"),
                    "description": item.get("description"),
                })

                ext_pas = item.get("extended_people_also_search")
                if isinstance(ext_pas, list):
                    for kw in ext_pas:
                        if isinstance(kw, str):
                            people_also_search.append(kw)
                        elif isinstance(kw, dict):
                            people_also_search.append(kw.get("keyword") or kw.get("title") or str(kw))

            elif item_type == "people_also_ask":
                for paa_item in item.get("items", []) or []:
                    question = (
                        paa_item.get("question")
                        or paa_item.get("title")
                        or paa_item.get("text")
                    )
                    if question:
                        paa.append({
                            "question": question,
                            "answer": paa_item.get("answer") or paa_item.get("snippet") or paa_item.get("text")
                        })

            elif item_type == "related_searches":
                for rel in item.get("items", []) or []:
                    if isinstance(rel, str):
                        related_searches.append(rel)
                    elif isinstance(rel, dict):
                        related_searches.append(rel.get("keyword") or rel.get("title") or str(rel))

            elif item_type in ("people_also_search", "people_also_search_for"):
                for rel in item.get("items", []) or []:
                    if isinstance(rel, str):
                        people_also_search.append(rel)
                    elif isinstance(rel, dict):
                        people_also_search.append(rel.get("keyword") or rel.get("title") or str(rel))

            elif item_type == "ai_overview":
                ai_texts: List[str] = []
                for ai_item in item.get("items", []) or []:
                    if ai_item.get("type") in ("ai_overview_element", "ai_overview_text") and ai_item.get("text"):
                        ai_texts.append(ai_item.get("text"))
                ai_overview = {
                    "text": "\n".join(ai_texts).strip() if ai_texts else None,
                    "references": item.get("references") or []
                }

        return {
            "organic": organic,
            "people_also_ask": paa,
            "people_also_search": self._dedupe_list(people_also_search),
            "related_searches": self._dedupe_list(related_searches),
            "ai_overview": ai_overview,
            "raw_item_types": item_types
        }

    # ========================================
    # Autocomplete
    # ========================================
    def _fetch_autocomplete(self, keyword: str, location_code: int, language_code: str) -> Dict[str, Any]:
        payload = [{
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code
        }]
        task_id = self._task_post("v3/serp/google/autocomplete/task_post", payload)
        task = self._task_get("v3/serp/google/autocomplete/task_get/advanced", task_id, max_wait=60, poll_interval=2)
        result = (task.get("result") or [])
        if not result:
            raise RuntimeError("No Autocomplete result returned")
        return result[0]

    def _parse_autocomplete(self, result: Dict[str, Any]) -> List[str]:
        items = result.get("items", []) or []
        suggestions: List[str] = []
        for item in items:
            if isinstance(item, str):
                suggestions.append(item)
            elif isinstance(item, dict):
                suggestions.append(item.get("keyword") or item.get("title") or item.get("text") or str(item))
        return self._dedupe_list(suggestions)

    # ========================================
    # Search Volume
    # ========================================
    def _fetch_search_volume(self, keywords: List[str], location_code: int, language_code: str) -> Dict[str, Any]:
        if not keywords:
            return {}

        keyword_chunks = self._chunk_list(keywords, 1000)
        results: Dict[str, Any] = {}

        for chunk in keyword_chunks:
            payload = [{
                "keywords": chunk,
                "location_code": location_code,
                "language_code": language_code
            }]
            task_id = self._task_post("v3/keywords_data/google_ads/search_volume/task_post", payload)
            task = self._task_get("v3/keywords_data/google_ads/search_volume/task_get", task_id, max_wait=120, poll_interval=3)
            result = (task.get("result") or [])
            if not result:
                continue
            for item in result[0].get("items", []) or []:
                kw = item.get("keyword")
                if not kw:
                    continue
                results[kw] = {
                    "search_volume": item.get("search_volume"),
                    "competition": item.get("competition"),
                    "cpc": item.get("cpc"),
                    "monthly_searches": item.get("monthly_searches")
                }

        return results

    # ========================================
    # Helpers
    # ========================================
    def _write_outputs(self, run_id: str, output: Dict[str, Any]) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        json_path = os.path.join(self.output_dir, f"{run_id}.json")
        txt_path = os.path.join(self.output_dir, f"{run_id}.txt")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(self._format_txt(output))

    def _format_txt(self, output: Dict[str, Any]) -> str:
        lines: List[str] = []
        lines.append(f"RUN_ID: {output.get('run_id')}")
        lines.append(f"SEED_KEYWORDS: {', '.join(output.get('seed_keywords', []))}")
        stats = output.get("stats", {})
        lines.append(f"TOTAL_KEYWORDS: {stats.get('total_keywords')}")
        lines.append(f"DURATION_SECONDS: {stats.get('duration_seconds')}")
        lines.append("")

        for kw, data in output.get("keywords", {}).items():
            lines.append("=" * 80)
            lines.append(f"KEYWORD: {kw}")
            lines.append(f"SOURCES: {', '.join(data.get('sources', []))}")
            sv = data.get("search_volume") or {}
            if sv:
                lines.append(f"SEARCH_VOLUME: {sv.get('search_volume')} | COMP: {sv.get('competition')} | CPC: {sv.get('cpc')}")
            else:
                lines.append("SEARCH_VOLUME: -")

            serp = data.get("serp", {})
            ai = serp.get("ai_overview")
            if ai and (ai.get("text") or ai.get("references")):
                lines.append("AI_OVERVIEW:")
                if ai.get("text"):
                    lines.append(ai.get("text"))
                if ai.get("references"):
                    lines.append(f"References: {len(ai.get('references', []))}")

            paa = serp.get("people_also_ask") or []
            if paa:
                lines.append("PAA:")
                for item in paa[:20]:
                    lines.append(f"- {item.get('question')}")

            pas = serp.get("people_also_search") or []
            if pas:
                lines.append("PEOPLE_ALSO_SEARCH:")
                for item in pas[:20]:
                    lines.append(f"- {item}")

            rel = serp.get("related_searches") or []
            if rel:
                lines.append("RELATED_SEARCHES:")
                for item in rel[:20]:
                    lines.append(f"- {item}")

            ac = data.get("autocomplete") or []
            if ac:
                lines.append("AUTOCOMPLETE:")
                for item in ac[:20]:
                    lines.append(f"- {item}")

            organic = serp.get("organic") or []
            if organic:
                lines.append("ORGANIC:")
                for item in organic[:20]:
                    lines.append(f"- {item.get('title')} | {item.get('url')}")

            lines.append("")

        return "\n".join(lines)

    def _normalize_keywords(self, keywords: List[str]) -> List[str]:
        cleaned = []
        for kw in keywords:
            nk = self._normalize_keyword(kw)
            if nk and nk not in cleaned:
                cleaned.append(nk)
        return cleaned

    def _normalize_keyword(self, keyword: Optional[str]) -> str:
        if not keyword:
            return ""
        return " ".join(keyword.strip().split())

    def _add_source(self, sources: Dict[str, Set[str]], keyword: str, source: str) -> None:
        nk = self._normalize_keyword(keyword)
        if not nk:
            return
        sources.setdefault(nk, set()).add(source)

    def _dedupe_list(self, items: List[Any]) -> List[Any]:
        seen = set()
        out = []
        for item in items:
            key = str(item).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    def _chunk_list(self, items: List[str], size: int) -> List[List[str]]:
        return [items[i:i + size] for i in range(0, len(items), size)]

    def _first_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        tasks = data.get("tasks") or []
        if not tasks:
            raise RuntimeError("DataForSEO response missing tasks")
        return tasks[0]

    def _task_error(self, task: Dict[str, Any]) -> Optional[str]:
        status_code = task.get("status_code")
        status_message = task.get("status_message")
        if status_code and status_code != 20000 and status_code not in (20100, 20101, 20102):
            return f"status_code={status_code}: {status_message}"
        return None
