import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PropertyLookup(models.Model):
    """One completed address-verification + building-information lookup for the
    wizard's step 2 ("Din nåværende bolig").

    The wizard submits only `token` (opaque). The server reloads this row at
    submit time and never trusts hidden form JSON — see apps.leads.views.wizard.
    Only the NORMALIZED structure is stored, never the raw provider response
    (privacy: no owner/occupant data is ever kept even if a provider returns it).
    """

    token = models.CharField(max_length=32, unique=True, editable=False)
    # Which BuildingDataProvider produced `normalized` ("mock" | "norkart" | …).
    provider = models.CharField(max_length=20)
    # The Kartverket-verified origin address this lookup ran for
    # (kartverket.verify_address output: {address, property, unit_numbers}).
    verified_address = models.JSONField()
    # {address, property, building, buildings, floors, units} — our internal
    # shape, provider-agnostic. Never the upstream payload.
    normalized = models.JSONField()
    # Set when the building had several boenheter and the customer picked one.
    selected_unit_number = models.CharField(max_length=20, blank=True, default="")
    # "api" — every value came from the registry. "user" — the customer
    # corrected at least one value (manual_overrides holds which).
    data_source = models.CharField(max_length=10, default="api")
    manual_overrides = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        addr = (self.verified_address or {}).get("address", {}).get("formatted")
        return addr or self.token

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        super().save(*args, **kwargs)


class MoveLead(models.Model):
    """
    One submitted /wizard request. Field set and validation rules mirror
    the WizardData shape in kobly-full-site-spec.pdf §5.4 exactly — this
    model is the Django-side contract the wizard form/view fill in.
    """

    FLYTTE_TYPE_CHOICES = [
        ("privat", "Privat"),
        ("bedrift", "Bedrift"),
        ("internasjonal", "Internasjonal"),
    ]
    BOLIGTYPE_CHOICES = [
        ("leilighet", "Leilighet"),
        ("rekkehus", "Rekkehus"),
        ("enebolig", "Enebolig"),
        ("annet", "Annet"),
    ]
    STATUS_CHOICES = [
        ("new", "Ny"),
        ("contacted", "Kontaktet"),
        ("booked", "Bestilt"),
    ]

    # Auto-generated in save(), e.g. "KOB-2026-42" — used as the customer-facing
    # reference number in the receipt email (spec §12 LEAD.ref).
    reference = models.CharField(max_length=32, unique=True, editable=False, blank=True)

    # Internal pipeline state, set/changed only from the staff dashboard —
    # never part of WizardForm, so every lead starts "new" by default.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")

    # Step 2
    flytte_type = models.CharField(max_length=20, choices=FLYTTE_TYPE_CHOICES)
    boligtype = models.CharField(max_length=20, choices=BOLIGTYPE_CHOICES)

    # Step 1 — coordinates are optional (spec §5.5: "coordinates NOT required" to advance)
    fra = models.CharField(max_length=255)
    fra_lat = models.FloatField(null=True, blank=True)
    fra_lon = models.FloatField(null=True, blank=True)
    til = models.CharField(max_length=255)
    til_lat = models.FloatField(null=True, blank=True)
    til_lon = models.FloatField(null=True, blank=True)

    # Step 3 — date XOR flexible, enforced in WizardForm.clean(), not here
    flyttedato = models.DateField(null=True, blank=True)
    fleksibel = models.BooleanField(default=False)

    # Step 4 — always-optional
    beskrivelse = models.TextField(blank=True, default="")

    # Step 5
    navn = models.CharField(max_length=200)
    telefon = models.CharField(max_length=50)
    epost = models.EmailField()

    # Normalized copies of telefon/epost (digits-only phone, lowercased email),
    # maintained in save(). Indexed so repeat-submission detection
    # (apps.leads.duplicates) is an exact index lookup, not a fuzzy scan.
    telefon_normalisert = models.CharField(max_length=20, blank=True, default="", db_index=True)
    epost_normalisert = models.CharField(max_length=254, blank=True, default="", db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # Step 2 — property / building information for the origin address, looked up
    # via apps.leads.property. All optional: a lead whose lookup failed (or who
    # skipped it) still saves. `property_lookup` is the full record;
    # the bolig_* columns are the denormalized headline values so the dashboard,
    # receipt email, and any future matching don't have to dig through JSON.
    property_lookup = models.ForeignKey(
        "PropertyLookup", null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    bolig_adresse = models.CharField(max_length=255, blank=True, default="")
    bolig_type = models.CharField(max_length=100, blank=True, default="")
    bolig_bra_m2 = models.PositiveIntegerField(null=True, blank=True)
    bolig_byggeaar = models.PositiveIntegerField(null=True, blank=True)
    bolig_etasjer = models.PositiveIntegerField(null=True, blank=True)
    bolig_enhet = models.CharField(max_length=20, blank=True, default="")  # e.g. "H0201"
    bolig_datakilde = models.CharField(max_length=10, blank=True, default="")  # "api" | "user" | ""
    bolig_gnr = models.CharField(max_length=10, blank=True, default="")
    bolig_bnr = models.CharField(max_length=10, blank=True, default="")

    # Staff-only fields — never part of WizardForm, never shown to the customer.
    internal_notes = models.TextField(blank=True, default="")
    follow_up_at = models.DateField(null=True, blank=True)

    # Soft delete: "Slett" in the dashboard archives rather than removing the
    # row outright, so a lead can be recovered from the trash view. A
    # genuine, permanent delete is only available from there.
    archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Repeat submission: the same person (phone OR email) sent another
    # forespørsel within apps.leads.duplicates.DUPLICATE_WINDOW and confirmed
    # they wanted a new one anyway. A flagged duplicate is NEVER auto-assigned
    # (apps.leads.views.wizard) — a staff member must decide, from the lead
    # detail page, whether to assign it or clear the flag.
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="duplicate_submissions"
    )

    # Manual staff assignment to up to 3 businesses (dashboard:lead_detail).
    # MoveLead is the live lead pipeline; store.JobDistribution's FK is
    # hard-typed to the separate, unreachable core.Flytteforesporsel model
    # (see docs/superpowers/specs/2026-08-21-dashboard-cms-and-business-admin-design.md
    # "Resolved: which lead pipeline is live"), so it can't represent an
    # assignment against a real MoveLead — these are their own fields
    # rather than repurposing that model.
    business_1 = models.ForeignKey(
        "store.Bedrift_info", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_leads_primary"
    )
    business_2 = models.ForeignKey(
        "store.Bedrift_info", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_leads_secondary"
    )
    business_3 = models.ForeignKey(
        "store.Bedrift_info", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_leads_tertiary"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.navn}"

    def clean(self):
        # apps.dashboard.views.lead_assign_businesses already blocks
        # assigning the same business to two of the three slots, but that
        # guard lives only in that one view — Django's own /admin/ (a plain
        # ModelAdmin, no equivalent check) can still save a MoveLead with,
        # say, business_1 == business_2. That's not just redundant: every
        # per-business lead count in the dashboard (_lead_counts_by_business,
        # business_list's annotations) tallies business_1/2/3 as three
        # independent GROUP BYs summed together, so a lead in two slots for
        # the same business is counted twice. ModelForm.is_valid() (which
        # the admin's own form uses) calls full_clean(), so this is
        # enforced there automatically, not just in the dashboard.
        super().clean()
        assigned = [b for b in (self.business_1_id, self.business_2_id, self.business_3_id) if b]
        if len(assigned) != len(set(assigned)):
            raise ValidationError("Samme bedrift kan ikke tildeles flere ganger på samme forespørsel.")

    def save(self, *args, **kwargs):
        # Generated before the first (and only) save, using a random component
        # instead of self.pk — a two-phase save (insert, then a second save
        # setting reference from the new pk) is vulnerable to a lost-lead
        # IntegrityError when two submissions' first inserts interleave, since
        # both would briefly try to write the same reference="" value against
        # this field's unique constraint.
        if not self.reference:
            self.reference = f"KOB-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}"
        # Keep the normalized contact columns in sync on every save — cheap,
        # and it means a lead edited in /admin/ stays detectable too.
        from .duplicates import normalize_email, normalize_phone
        self.telefon_normalisert = normalize_phone(self.telefon)
        self.epost_normalisert = normalize_email(self.epost)
        super().save(*args, **kwargs)


class LeadImage(models.Model):
    """One uploaded photo attached to a MoveLead (spec §5.8 'bilder')."""

    lead = models.ForeignKey(MoveLead, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="leads/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.lead.reference}"
