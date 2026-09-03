from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import *

phone_validator = RegexValidator(
    regex=r"^[0-9+\-\s()]{6,20}$",
    message="Skriv inn et gyldig telefonnummer (tall, mellomrom og +/-/() tillatt).",
)

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_max_file_size(value):
    """Applied to every business logo/gallery-photo upload. ImageField on its
    own only checks the upload decodes as an image (via Pillow) — it never
    bounded file size, so a logged-in business could previously upload up
    to 6 arbitrarily large "images" with no per-file limit."""
    if value.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(f"Filen er for stor. Maks {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.")


class Bedrift_info(models.Model):
    # Relation to User (linked after signup)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name="bedrift_info")

    # Step 1
    move_type = models.CharField(max_length=255, blank=True, null=True)  # comma-separated

    # Step 2
    cities = models.CharField(max_length=255, blank=True, null=True)  # comma-separated

    # Structured coverage — one entry per place the business serves, each with
    # a pickup/dropoff (one-way vs two-way) flag:
    #   [{"place": "Oslo", "pickup": true, "dropoff": true}, ...]
    # `cities` above is kept as the flat, legacy comma list (matching + older
    # UI still read it); service_areas is the richer source the onboarding
    # flow and lead matching prefer when present.
    service_areas = models.JSONField(default=list, blank=True)

    # Step 3
    company_name = models.CharField(max_length=255)
    company_number = models.CharField(max_length=50, blank=True, null=True)
    employees = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=50, validators=[phone_validator])
    website = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)

    # Step 4
    tiltaleform = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)


    # Leads information
    leads_per_day = models.CharField(max_length=90, blank=True, null=True)
    leads_per_week = models.CharField(max_length=90, blank=True, null=True)
    leads_per_month = models.CharField(max_length=90, blank=True, null=True)


    total_leads_received = models.PositiveIntegerField(default=0)

    # Selskaper mann skal prioritere ettersom andre har nådd grensa. Så går det etter listen. 1-10, hvor 10 er best
    priority_score = models.PositiveIntegerField(default=0)

    active = models.BooleanField(default=False)

    # Staff-only categorization, e.g. "VIP, treg respons" — never shown on
    # the business's own public profile or account pages.
    tags = models.CharField(max_length=255, blank=True, default="")
    internal_notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.company_name:
            return f"{self.company_name} ({self.email})"
        return f"{self.email}"



class PublicBusinessInformation(models.Model):
    business = models.OneToOneField(
        Bedrift_info,
        on_delete=models.CASCADE,
        related_name="public_info"
    )
    logo = models.ImageField(upload_to="business_logos/", blank=True, null=True, validators=[validate_max_file_size])
    about_us = models.TextField(blank=True, null=True)
    faq = models.TextField(blank=True, null=True, help_text="Use line breaks to separate questions/answers.")

    def __str__(self):
        return f"Public info for {self.business.company_name}"


class BusinessImage(models.Model):
    public_info = models.ForeignKey(
        "PublicBusinessInformation",
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="business_images/", validators=[validate_max_file_size])

    def clean(self):
        if self.public_info.images.count() >= 6 and not self.pk:
            raise ValidationError("Du kan maksimalt laste opp 6 bilder.")

    def __str__(self):
        return f"Image for {self.public_info.business.company_name}"



class Review(models.Model):
    business = models.ForeignKey(
        Bedrift_info,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(default=5, choices=[(i, f"{i} ⭐") for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating}⭐ by {self.name} for {self.business.company_name}"


class JobDistribution(models.Model):
    inquiry = models.ForeignKey(
        "core.Flytteforesporsel",
        on_delete=models.CASCADE,
        related_name="distributions"
    )

    # 🧩 Three business slots
    business_1 = models.ForeignKey(
        "store.Bedrift_info",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distribution_primary",
        verbose_name="Business 1"
    )
    business_2 = models.ForeignKey(
        "store.Bedrift_info",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distribution_secondary",
        verbose_name="Business 2"
    )
    business_3 = models.ForeignKey(
        "store.Bedrift_info",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distribution_tertiary",
        verbose_name="Business 3"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)

    def __str__(self):
        names = [b.company_name for b in [self.business_1, self.business_2, self.business_3] if b]
        return f"Distribution for {self.inquiry} → {', '.join(names)}"

    def businesses(self):
        """Convenience list of the businesses assigned here."""
        return [b for b in [self.business_1, self.business_2, self.business_3] if b]


class CoverageChangeRequest(models.Model):
    """A business's requested change to its Dekning (services + cities +
    structured service areas). Submitting from the account portal no longer
    edits Bedrift_info directly — it stages one of these for an admin to
    approve, so a business's coverage can never silently drift and staff
    always see who wants to change what."""

    STATUS_CHOICES = [
        ("pending", "Venter på godkjenning"),
        ("approved", "Godkjent"),
        ("rejected", "Avvist"),
    ]

    business = models.ForeignKey(
        Bedrift_info, on_delete=models.CASCADE, related_name="coverage_requests"
    )
    move_type = models.CharField(max_length=255, blank=True, default="")
    cities = models.CharField(max_length=255, blank=True, default="")
    service_areas = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Dekningsendring — {self.business.company_name} ({self.get_status_display()})"

    @property
    def areas_label(self):
        """Readable summary of the structured service_areas, e.g.
        "Oslo ↔, Drammen →, Asker ←" — used in the admin warnings so staff
        see the *extra* places, not just the flat main-city list."""
        arrows = {(True, True): "↔", (True, False): "→", (False, True): "←"}
        parts = []
        for entry in self.service_areas or []:
            place = entry.get("place")
            if not place:
                continue
            key = (bool(entry.get("pickup", True)), bool(entry.get("dropoff", True)))
            parts.append(f"{place} {arrows.get(key, '↔')}")
        return ", ".join(parts)


class LeadCredit(models.Model):
    """A "this was a bad lead" report for one (lead, business) pair. Raised
    from the business account or the admin lead page; once an admin approves
    it the lead is credited — excluded from that business's invoice totals —
    and the status is shown on the lead page, the account, and the PDF
    invoice."""

    STATUS_CHOICES = [
        ("requested", "Meldt"),
        ("approved", "Kreditert"),
        ("rejected", "Avslått"),
    ]

    lead = models.ForeignKey(
        "leads.MoveLead", on_delete=models.CASCADE, related_name="credits"
    )
    business = models.ForeignKey(
        Bedrift_info, on_delete=models.CASCADE, related_name="lead_credits"
    )
    reason = models.TextField(blank=True, default="")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="requested")
    created_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["lead", "business"], name="unique_lead_credit_per_business"),
        ]

    def __str__(self):
        return f"Kreditt — {self.lead.reference} / {self.business.company_name} ({self.get_status_display()})"


class InvoiceRun(models.Model):
    """A ledger row written every time a staff member generates an invoice
    PDF (per-business or bulk). It records what period was billed and the
    totals at that moment, so the Økonomi page can tell "delivered but not
    yet invoiced" leads from ones already on a sent invoice — the PDF
    endpoints themselves are stateless and would otherwise leave no trace
    of what has been billed.

    A per-business run has `business` set. A bulk run writes one row per
    business it covered (so each business's own billed-through date is
    still correct), all sharing the same `batch` uuid."""

    KIND_CHOICES = [
        ("single", "Enkeltfaktura"),
        ("bulk", "Samlefaktura"),
    ]

    business = models.ForeignKey(
        Bedrift_info, on_delete=models.CASCADE, related_name="invoice_runs"
    )
    kind = models.CharField(max_length=8, choices=KIND_CHOICES, default="single")
    batch = models.CharField(max_length=32, blank=True, default="", db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    lead_count = models.PositiveIntegerField(default=0)
    credited_count = models.PositiveIntegerField(default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    generated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [models.Index(fields=["business", "-period_end"])]

    def __str__(self):
        return f"Faktura — {self.business.company_name} ({self.period_start}–{self.period_end})"
