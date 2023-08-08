from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHelpdeskTicketTeam(TransactionCase):
    def setUp(self):
        super().setUp()
        self.HelpdeskTicketTeam = self.env["helpdesk.ticket.team"]
        self.HelpdeskTicket = self.env["helpdesk.ticket"]
        self.ResUsers = self.env["res.users"]

        self.user1 = self.ResUsers.create(
            {"name": "User 1", "login": "user1@example.com"}
        )
        self.user2 = self.ResUsers.create(
            {"name": "User 2", "login": "user2@example.com"}
        )
        self.user3 = self.ResUsers.create(
            {"name": "User 3", "login": "user3@example.com"}
        )

        self.team1 = self.HelpdeskTicketTeam.create(
            {
                "name": "Team 1",
                "user_ids": [(6, 0, [self.user1.id, self.user2.id, self.user3.id])],
                "assign_method": "manual",
            }
        )

    def test_assign_method(self):
        self.team1.assign_method = "randomly"
        self.assertEqual(self.team1.assign_method, "randomly")

        self.team1.assign_method = "balanced"
        self.assertEqual(self.team1.assign_method, "balanced")

        self.team1.assign_method = "sequential"
        self.assertEqual(self.team1.assign_method, "sequential")

        self.team1.assign_method = "manual"
        self.team1.user_ids = [(5,)]
        with self.assertRaises(ValidationError):
            self.team1.assign_method = "randomly"

    def test_get_new_user(self):
        new_user = self.team1.get_new_user()
        self.assertEqual(new_user, self.ResUsers)

        self.team1.assign_method = "randomly"
        new_user = self.team1.get_new_user()
        self.assertIn(new_user, self.team1.user_ids)

        self.team1.assign_method = "balanced"
        new_user = self.team1.get_new_user()
        self.assertIn(new_user, self.team1.user_ids)

        self.team1.assign_method = "sequential"
        new_user = self.team1.get_new_user()
        self.assertIn(new_user, self.team1.user_ids)

    def test_create_ticket(self):
        self.team1.assign_method = "randomly"
        ticket = self.HelpdeskTicket.create(
            {
                "name": "Test Ticket",
                "description": "Test Ticket Description",
                "team_id": self.team1.id,
            }
        )
        self.assertIn(ticket.user_id, self.team1.user_ids)

        self.team1.assign_method = "balanced"
        ticket = self.HelpdeskTicket.create(
            {
                "name": "Test Ticket",
                "description": "Test Ticket Description",
                "team_id": self.team1.id,
            }
        )
        self.assertIn(ticket.user_id, self.team1.user_ids)

        self.team1.assign_method = "sequential"
        for i in range(10):
            ticket = self.HelpdeskTicket.create(
                {
                    "name": "Test Ticket {}".format(i + 1),
                    "description": "Test Ticket Description {}".format(i + 1),
                    "team_id": self.team1.id,
                }
            )

        ticket_count = {
            user: self.HelpdeskTicket.search_count([("user_id", "=", user.id)])
            for user in self.team1.user_ids
        }

        num_tickets_per_user = next(iter(ticket_count.values()))
        for count in ticket_count.values():
            self.assertEqual(count, num_tickets_per_user)
