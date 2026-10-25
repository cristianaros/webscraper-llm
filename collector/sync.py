"""Authenticated central API client; it never contains central persistence logic."""
from __future__ import annotations
import httpx
from collector.config import CollectorSettings
from shared.contracts import Delivery, ImageDelivery, MediaReceipt, Receipt, RunReport, RunRequest, SourceConfig

class SyncClient:
    def __init__(self,settings:CollectorSettings,client:httpx.Client): self.settings,self.client=settings,client
    @property
    def headers(self): return {'Authorization':f'Bearer {self.settings.collector_token.get_secret_value() if self.settings.collector_token else ""}'}
    def sources(self):
        r = self.client.get(f'{self.settings.api_url}/api/collector/sources', headers=self.headers)
        r.raise_for_status()
        data = r.json()
        items = data.get("sources", data) if isinstance(data, dict) else data
        return [SourceConfig.model_validate(x) for x in items]
    def send(self,delivery:Delivery)->Receipt:
        r=self.client.post(f'{self.settings.api_url}/api/collector/articles',headers=self.headers,json=delivery.model_dump(mode='json')); r.raise_for_status(); return Receipt.model_validate(r.json())
    def report(self,report:RunReport)->None: self.client.put(f'{self.settings.api_url}/api/collector/runs/{report.run_id}',headers=self.headers,json=report.model_dump(mode='json')).raise_for_status()
    def claim_runs(self) -> list[RunRequest]:
        response = self.client.post(f'{self.settings.api_url}/api/collector/runs/claim', headers=self.headers, json={'collector_id': self.settings.collector_id})
        response.raise_for_status()
        return [RunRequest.model_validate(item) for item in response.json()]
    def renew_run(self, request: RunRequest):
        response = self.client.post(f'{self.settings.api_url}/api/collector/runs/{request.run_id}/renew', headers=self.headers, json={'lease_token': str(request.lease_token)})
        response.raise_for_status()
        return response.json()
    def report_claimed(self, report: RunReport, request: RunRequest) -> None:
        headers = {**self.headers, 'X-Lease-Token': str(request.lease_token)}
        response = self.client.put(f'{self.settings.api_url}/api/collector/runs/{report.run_id}', headers=headers, json=report.model_dump(mode='json'))
        response.raise_for_status()
    def send_media(self, delivery: ImageDelivery, data: bytes) -> MediaReceipt:
        """The image bytes are uploaded only after their hash was verified locally."""
        response = self.client.post(
            f'{self.settings.api_url}/api/collector/media', headers=self.headers,
            data={'delivery': delivery.model_dump_json()},
            files={'file': ('original', data, delivery.image.content_type or 'application/octet-stream')},
        )
        response.raise_for_status()
        return MediaReceipt.model_validate(response.json())
    def heartbeat(self,status:dict)->None: self.client.put(f'{self.settings.api_url}/api/collector/status',headers=self.headers,json=status).raise_for_status()
