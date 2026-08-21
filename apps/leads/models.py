import uuid

from django.db import models
from django.utils import timezone


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

    # Auto-generated in save(), e.g. "KOB-2026-42" — used as the customer-facing
    # reference number in the receipt email (spec §12 LEAD.ref).
    reference = models.CharField(max_length=32, unique=True, editable=False, blank=True)

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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.navn}"

    def save(self, *args, **kwargs):
        # Generated before the first (and only) save, using a random component
        # instead of self.pk — a two-phase save (insert, then a second save
        # setting reference from the new pk) is vulnerable to a lost-lead
        # IntegrityError when two submissions' first inserts interleave, since
        # both would briefly try to write the same reference="" value against
        # this field's unique constraint.
        if not self.reference:
            self.reference = f"KOB-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class LeadImage(models.Model):
    """One uploaded photo attached to a MoveLead (spec §5.8 'bilder')."""

    lead = models.ForeignKey(MoveLead, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="leads/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.lead.reference}"
