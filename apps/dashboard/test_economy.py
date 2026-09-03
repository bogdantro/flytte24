"""Tests for the Økonomi dashboard (apps/dashboard/economy.py + view)."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.dashboard import economy
from apps.leads.models import MoveLead
from apps.store.models import Bedrift_info, InvoiceRun, LeadCredit

PRICE = economy.PRICE_PER_LEAD


def _business(name, email, **extra):
    return Bedrift_info.objects.create(
        company_name=name, email=email, phone="+47 900 00 000",
        address="Gata 1", postal_code="0153", city="Oslo",
        first_name="Kari", last_name="Nordmann", active=extra.pop("active", True),
        **extra,
    )


def _lead(created, **overrides):
    data = dict(
        flytte_type="privat", fra="Kongens gate 1, 0153 Oslo",
        til="Storgata 14, 0184 Oslo", boligtype="leilighet",
        navn="Ola Nordmann", telefon="+47 900 00 000", epost="ola@eksempel.no",
    )
    data.update(overrides)
    lead = MoveLead.objects.create(**data)
    # created_at is auto_now_add — rewrite it through a queryset update.
    MoveLead.objects.filter(pk=lead.pk).update(
        created_at=timezone.make_aware(
            timezone.datetime(created.year, created.month, created.day, 12, 0)
        )
    )
    return MoveLead.objects.get(pk=lead.pk)


class ComputeTests(TestCase):
    def setUp(self):
        self.b1 = _business("Flyttebyrå A", "a@x.no")
        self.b2 = _business("Flyttebyrå B", "b@x.no")
        self.today = date(2026, 6, 15)

    def test_lead_to_two_businesses_is_two_billable_pairs(self):
        _lead(self.today, business_1=self.b1, business_2=self.b2)
        data = economy.compute(date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(data["lead_pairs"], 2)
        self.assertEqual(data["gross"], PRICE * 2)
        self.assertEqual(data["net"], PRICE * 2)

    def test_approved_credit_reduces_net(self):
        lead = _lead(self.today, business_1=self.b1, business_2=self.b2)
        LeadCredit.objects.create(lead=lead, business=self.b1, status="approved")
        data = economy.compute(date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(data["credited_pairs"], 1)
        self.assertEqual(data["net"], PRICE)

    def test_requested_credit_does_not_reduce_net(self):
        lead = _lead(self.today, business_1=self.b1)
        LeadCredit.objects.create(lead=lead, business=self.b1, status="requested")
        data = economy.compute(date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(data["net"], PRICE)

    def test_archived_lead_excluded(self):
        _lead(self.today, business_1=self.b1, archived=True)
        data = economy.compute(date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(data["net"], Decimal("0"))

    def test_unassigned_lead_earns_nothing(self):
        _lead(self.today)
        data = economy.compute(date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(data["net"], Decimal("0"))

    def test_out_of_range_lead_excluded(self):
        _lead(date(2026, 5, 20), business_1=self.b1)
        data = economy.compute(date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(data["net"], Decimal("0"))

    def test_by_business_rows_sorted_by_net_desc(self):
        _lead(self.today, business_1=self.b1)
        _lead(self.today, business_1=self.b2)
        _lead(self.today, business_2=self.b2)
        data = economy.compute(date(2026, 6, 1), date(2026, 6, 30))
        self.assertEqual(data["by_business"][0]["name"], "Flyttebyrå B")
        self.assertEqual(data["by_business"][0]["net"], PRICE * 2)


class UninvoicedTests(TestCase):
    def setUp(self):
        self.b1 = _business("Flyttebyrå A", "a@x.no")
        self.today = date(2026, 6, 15)

    def test_all_unbilled_when_no_invoice_run(self):
        _lead(date(2026, 6, 10), business_1=self.b1)
        result = economy.uninvoiced(today=self.today)
        self.assertEqual(result["total"], PRICE)
        self.assertIsNone(result["rows"][0]["since"])

    def test_leads_before_billed_through_are_excluded(self):
        _lead(date(2026, 6, 1), business_1=self.b1)
        _lead(date(2026, 6, 12), business_1=self.b1)
        InvoiceRun.objects.create(
            business=self.b1, period_start=date(2026, 6, 1), period_end=date(2026, 6, 5),
            lead_count=1, subtotal=PRICE, total=PRICE,
        )
        result = economy.uninvoiced(today=self.today)
        self.assertEqual(result["total"], PRICE)  # only the 12 June lead
        self.assertEqual(result["rows"][0]["since"], date(2026, 6, 5))

    def test_approved_credit_removed_from_uninvoiced(self):
        lead = _lead(date(2026, 6, 10), business_1=self.b1)
        LeadCredit.objects.create(lead=lead, business=self.b1, status="approved")
        result = economy.uninvoiced(today=self.today)
        self.assertEqual(result["total"], Decimal("0"))


class RecordInvoiceRunTests(TestCase):
    def test_record_from_build_invoice(self):
        from apps.store.invoicing import build_invoice

        b1 = _business("Flyttebyrå A", "a@x.no")
        _lead(date(2026, 6, 10), business_1=b1)
        start = timezone.make_aware(timezone.datetime(2026, 6, 1))
        end = timezone.make_aware(timezone.datetime(2026, 6, 30, 23, 59))
        run = economy.record_invoice_run(build_invoice(b1, start, end))
        self.assertEqual(run.period_start, date(2026, 6, 1))
        self.assertEqual(run.lead_count, 1)
        self.assertEqual(run.total, PRICE * (Decimal("1") + Decimal("0.25")))


class EconomyViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff", password="pw-12345", is_staff=True)
        self.client.login(username="staff", password="pw-12345")
        self.b1 = _business("Flyttebyrå A", "a@x.no")

    def test_requires_staff(self):
        self.client.logout()
        resp = self.client.get(reverse("dashboard:economy_dashboard"))
        self.assertEqual(resp.status_code, 302)

    def test_renders_with_data(self):
        _lead(timezone.localdate(), business_1=self.b1)
        resp = self.client.get(reverse("dashboard:economy_dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Flyttebyrå A")
        self.assertContains(resp, "Økonomi")

    def test_custom_range_filter(self):
        _lead(date(2026, 1, 10), business_1=self.b1)
        resp = self.client.get(
            reverse("dashboard:economy_dashboard"), {"from": "2026-01-01", "to": "2026-01-31"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "01.01.2026")

    def test_overview_shows_revenue_stat(self):
        _lead(timezone.localdate(), business_1=self.b1)
        resp = self.client.get(reverse("dashboard:dashboard_overview"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "eks. mva")

    def test_invoice_pdf_records_run(self):
        _lead(timezone.localdate(), business_1=self.b1)
        resp = self.client.get(
            reverse("dashboard:business_invoice_pdf", args=[self.b1.pk]), {"period": "month"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(InvoiceRun.objects.filter(business=self.b1, kind="single").count(), 1)
