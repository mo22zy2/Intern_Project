from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.template import context as context_module
from api.models import ReservationSystem


_patched = False
if not _patched:
    _orig_base_copy = context_module.BaseContext.__copy__
    _orig_render_copy = context_module.RenderContext.__copy__

    def _base_copy(self):
        duplicate = context_module.BaseContext({})
        duplicate.dicts = self.dicts[:]
        return duplicate

    def _render_copy(self):
        duplicate = context_module.RenderContext({})
        duplicate.dicts = self.dicts[:]
        return duplicate

    context_module.BaseContext.__copy__ = _base_copy
    context_module.RenderContext.__copy__ = _render_copy
    _patched = True


class TestMakeReservation(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.url = reverse("make_reservation")

    def _login(self):
        self.client.login(username="testuser", password="testpass123")

    def _valid_date(self):
        return (date.today() + timedelta(days=1)).isoformat()

    def test_requires_login(self):
        response = self.client.get(self.url)
        expected = f"{reverse('login')}?next={self.url}"
        self.assertRedirects(response, expected)

    def test_make_reservation_GET_renders_form(self):
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservation/reservation_form.html")

    def test_make_reservation_POST_creates_reservation(self):
        self._login()
        response = self.client.post(self.url, {
            "reservation_date": self._valid_date(),
            "reservation_time": "14:00",
            "seats": 4,
        })
        self.assertRedirects(response, reverse("my_reservations"))
        self.assertEqual(ReservationSystem.objects.count(), 1)
        reservation = ReservationSystem.objects.first()
        self.assertEqual(reservation.seats, 4)
        self.assertEqual(reservation.status, "pending")
        self.assertEqual(reservation.user, self.user)

    def test_make_reservation_past_date_rejected(self):
        self._login()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = self.client.post(self.url, {
            "reservation_date": yesterday,
            "reservation_time": "14:00",
            "seats": 4,
        }, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("past" in str(m).lower() for m in messages))
        self.assertEqual(ReservationSystem.objects.count(), 0)

    def test_make_reservation_invalid_hour_rejected(self):
        self._login()
        response = self.client.post(self.url, {
            "reservation_date": self._valid_date(),
            "reservation_time": "05:00",
            "seats": 4,
        }, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("hours" in str(m).lower() for m in messages))
        self.assertEqual(ReservationSystem.objects.count(), 0)

    def test_make_reservation_negative_seats_rejected(self):
        self._login()
        response = self.client.post(self.url, {
            "reservation_date": self._valid_date(),
            "reservation_time": "14:00",
            "seats": 0,
        }, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("invalid" in str(m).lower() for m in messages))
        self.assertEqual(ReservationSystem.objects.count(), 0)

    def test_make_reservation_missing_fields(self):
        self._login()
        response = self.client.post(self.url, {
            "reservation_date": "",
            "reservation_time": "14:00",
            "seats": 4,
        }, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("required" in str(m).lower() for m in messages))
        self.assertEqual(ReservationSystem.objects.count(), 0)


class TestMyReservations(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass123",
        )
        self.url = reverse("my_reservations")

    def _login(self):
        self.client.login(username="testuser", password="testpass123")

    def test_lists_user_reservations(self):
        ReservationSystem.objects.create(
            user=self.user, reservation_date="2025-12-25",
            reservation_time="19:00", seats=2,
        )
        ReservationSystem.objects.create(
            user=self.user, reservation_date="2025-12-26",
            reservation_time="20:00", seats=4,
        )
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reservation/my_reservations.html")
        self.assertEqual(len(response.context["reservations"]), 2)
        self.assertContains(response, "Reservation")

    def test_only_user_reservations_shown(self):
        ReservationSystem.objects.create(
            user=self.other_user, reservation_date="2025-12-25",
            reservation_time="19:00", seats=2,
        )
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["reservations"]), 0)

    def test_empty_list(self):
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reservations"]), 0)


class TestEditReservation(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.reservation = ReservationSystem.objects.create(
            user=self.user, reservation_date="2025-12-25",
            reservation_time="19:00", seats=4,
        )
        self.url = reverse("edit_reservation", args=[self.reservation.id])

    def _login(self):
        self.client.login(username="testuser", password="testpass123")

    def _valid_date(self):
        return (date.today() + timedelta(days=1)).isoformat()

    def test_edit_reservation_updates_fields(self):
        self._login()
        response = self.client.post(self.url, {
            "reservation_date": self._valid_date(),
            "reservation_time": "20:00",
            "seats": 6,
        })
        self.assertRedirects(response, reverse("my_reservations"))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.seats, 6)
        self.assertEqual(str(self.reservation.reservation_time), "20:00:00")

    def test_edit_cancelled_reservation_rejected(self):
        self.reservation.status = "cancelled"
        self.reservation.save()
        self._login()
        response = self.client.post(self.url, {
            "reservation_date": self._valid_date(),
            "reservation_time": "20:00",
            "seats": 6,
        }, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("cancelled" in str(m).lower() for m in messages))

    def test_edit_invalid_date_rejected(self):
        self._login()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = self.client.post(self.url, {
            "reservation_date": yesterday,
            "reservation_time": "20:00",
            "seats": 6,
        }, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("past" in str(m).lower() for m in messages))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.seats, 4)


class TestCancelReservation(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass123",
        )
        self.reservation = ReservationSystem.objects.create(
            user=self.user, reservation_date="2025-12-25",
            reservation_time="19:00", seats=4,
        )
        self.url = reverse("cancel_reservation", args=[self.reservation.id])

    def _login(self):
        self.client.login(username="testuser", password="testpass123")

    def test_cancel_reservation_changes_status(self):
        self._login()
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("my_reservations"))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "cancelled")

    def test_cancel_already_cancelled_shows_info(self):
        self.reservation.status = "cancelled"
        self.reservation.save()
        self._login()
        response = self.client.post(self.url, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already" in str(m).lower() for m in messages))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, "cancelled")

    def test_cancel_not_owner_404(self):
        self.client.login(username="other", password="testpass123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
