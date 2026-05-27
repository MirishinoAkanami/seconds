from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date


# ── Default AI knowledge base (watch shop only) ──────────────────────────────
DEFAULT_AI_KNOWLEDGE = """STORE ASSISTANT KNOWLEDGE BASE
================================

ABOUT THE STORE
---------------
- We are a watch shop and sari-sari store.
- We sell brand new, pre-owned, restored, and limited edition watches.
- We also offer watch repair and maintenance services.
- Payment is accepted via GCash or Pay at Shop (cash on pickup).
- Home delivery is available within our delivery area for an additional fee.
- Store pickup is also available at no extra charge.

WATCH SERVICES & REPAIRS
-------------------------
Important note: All repair prices listed below are ESTIMATES and AVERAGE RANGES only.
Final prices depend on the specific watch brand, model, movement type (quartz vs mechanical),
age of the watch, extent of damage, and availability of parts.
Please visit the store or contact us for an accurate quote.

- Watch battery replacement: Average range ₱130 - ₱340 depending on watch brand and battery type
- Watch strap replacement (rubber): Average range ₱140 - ₱200
- Watch strap replacement (leather): Average range ₱140 - ₱200
- Watch strap replacement (metal/bracelet): Average range ₱160 - ₱340
- Watch crystal / glass replacement: Price varies significantly by watch size and crystal type (mineral, sapphire, acrylic). Please bring the watch in for a quote.
- Watch cleaning and polishing: Price varies by condition and type of watch. Mechanical watches cost more to service than quartz.
- Full watch overhaul / servicing: Prices vary widely depending on movement type, brand, and number of parts needing replacement. Mechanical/automatic watches cost more than quartz.
- Watch hand repair: Price depends on type and availability of replacement hands
- Watch crown / stem repair: Price depends on brand and parts availability
- Water resistance restoration / pressure test: Price varies by watch type
- Wall clock repair: Price varies depending on type of clock (quartz wall clock, pendulum, chime, cuckoo) and what needs to be fixed. Simple battery/mechanism replacements are cheaper; antique or chime clocks cost more.
- Other repairs: Bring the clock or watch in for assessment — we will give a quote after checking.

HOW TO ORDER A WATCH
--------------------
1. Browse the watch catalog and find a watch you like.
2. Click "Reserve This Watch" on the watch detail page.
3. Choose your payment method: GCash or Pay at Shop.
4. Choose pickup or home delivery.
5. If paying via GCash, send the payment to our GCash number and enter your reference number.
6. Submit your reservation and wait for our confirmation.
7. We will contact you once your order is verified.

GCASH PAYMENT
-------------
- Send payment to our GCash number (visible on the order page and store info).
- Take a screenshot of your payment and upload it when reserving.
- Include your GCash reference number in the order form.
- Once verified by the admin, your order status will be updated.

DELIVERY INFORMATION
--------------------
- Home delivery is available within our designated delivery area.
- Delivery fee is shown on the order form before you confirm.
- You can track your order status in "My Orders" after logging in.

ORDER STATUSES (what they mean)
--------------------------------
- Pending: Your reservation was received and is waiting for review.
- Verified: Your payment was confirmed and order is accepted.
- Preparing: Your watch is being prepared for delivery or pickup.
- Out for Delivery: Your watch is on its way to you.
- Ready for Pickup: Your watch is ready to be picked up at the store.
- Delivered: Your order has been completed.
- Cancelled/Rejected: The order was not processed.

FREQUENTLY ASKED QUESTIONS
---------------------------
Q: Can I reserve a watch without paying first?
A: Yes! Choose "Pay at Shop" as your payment method and pay when you pick it up.

Q: How long does it take to verify my GCash payment?
A: Usually within the same business day. We will update your order status once verified.

Q: Can I cancel my order?
A: Yes, you can cancel while your order is still in "Pending" status from your My Orders page.

Q: Do you accept layaway?
A: No, we do not offer layaway at this time.

Q: What watch brands do you carry?
A: Our available watches vary depending on current stock. Browse the Watches page to see what is available right now.

Q: Do you buy second-hand watches?
A: Yes, we do buy second-hand watches! Visit the store or contact us directly to discuss.

Q: How much does it cost to repair my watch?
A: Repair costs depend on the type of watch, the brand, the extent of the damage, and what parts are needed. The prices listed above are estimates and average ranges only. We recommend visiting the store or contacting us so we can assess the watch and give you an accurate quote.

Q: How do I know if a watch is still available?
A: You can browse the Watches page — only available watches are shown there.

Q: Can I visit the shop in person?
A: Yes! Come visit us during our store hours. Our address and hours are shown on this page.

Q: I have a question not answered here.
A: Please contact us directly via our GCash number or visit the store. We are happy to help!

IMPORTANT NOTE FOR AI
---------------------
- Only answer questions related to watches, watch services, ordering, delivery, GCash, and store info.
- Do not reveal any information about sari-sari store inventory, stock levels, or item prices.
- If asked about sari-sari items, politely say that information is not available through the assistant.
- Always be friendly, helpful, and concise.
- If you do not know the exact answer, give the best general guidance and suggest contacting the store.
- For repair prices, always remind the customer that prices are estimates and vary by watch type and condition.
"""


class CustomUser(AbstractUser):
    ROLE_CHOICES = [('user', 'User'), ('admin', 'Admin')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    contact_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    birthday = models.DateField(null=True, blank=True)
    agreed_to_terms = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    @property
    def age(self):
        if self.birthday:
            today = date.today()
            return today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day)
            )
        return None

    @property
    def is_admin_user(self):
        return self.is_superuser or self.role == 'admin'

    def __str__(self):
        return self.username


class Announcement(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='announcements/', blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title


class StoreSettings(models.Model):
    store_name = models.CharField(max_length=100, default='EJ&ELLA Store')
    gcash_number = models.CharField(max_length=20, default='09000000000')
    gcash_name = models.CharField(max_length=100, default='Store Owner')
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=50.00)
    delivery_area = models.CharField(max_length=300, default='Surigao City, Surigao del Norte')
    store_address = models.TextField(default='')
    store_hours = models.CharField(max_length=200, default='Mon-Sat: 8AM - 7PM')
    facebook_page_url = models.URLField(blank=True, default='')
    ai_store_info = models.TextField(blank=True, default='')
    groq_api_key = models.CharField(max_length=200, blank=True, default='', help_text='Your Groq API key. Get one free at console.groq.com')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Store Settings'

    def __str__(self):
        return 'Store Settings'

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        # Auto-populate AI knowledge with default if empty
        if created or not obj.ai_store_info.strip():
            obj.ai_store_info = DEFAULT_AI_KNOWLEDGE
            obj.save()
        return obj

    def get_ai_knowledge(self):
        """Returns the AI knowledge, falling back to default if empty."""
        if self.ai_store_info and self.ai_store_info.strip():
            return self.ai_store_info
        return DEFAULT_AI_KNOWLEDGE
