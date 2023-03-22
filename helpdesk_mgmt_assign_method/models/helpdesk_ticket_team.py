# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HelpdeskTicketTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    assign_method = fields.Selection(
        [("manual", "Manually"), ("randomly", "Randomly"), ("balanced", "Balanced")],
        string="Assignation Method",
        default="manual",
        required=True,
        help="Automatic assignation method for new tickets:\n"
        "\tManually: manual\n"
        "\tRandomly: randomly but everyone gets the same amount\n"
        "\tBalanced: to the person with the least amount of open tickets",
    )

    @api.onchange("user_ids")
    def _onchange_user_ids(self):
        if not self.user_ids:
            self.assign_method = "manual"

    @api.constrains("assign_method", "user_ids")
    def _check_user_assignation(self):
        if not self.user_ids and self.assign_method != "manual":
            raise ValidationError(
                _(
                    "You must have team members assigned to change the assignation method."
                )
            )

    @api.multi
    def get_new_user(self):
        self.ensure_one()
        new_user = self.env["res.users"]
        user_ids = sorted(self.user_ids.ids)

        if not user_ids:
            return new_user

        if self.assign_method == "randomly":
            return self._assign_randomly(user_ids, new_user)

        if self.assign_method == "balanced":
            return self._assign_balanced(user_ids, new_user)

        return new_user

    def _assign_randomly(self, user_ids, new_user):
        # Find the previously assigned user
        previous_assigned_user = (
            self.env["helpdesk.ticket"]
            .search(
                [("team_id", "=", self.id)],
                order="create_date desc, id desc",
                limit=1,
            )
            .user_id
        )

        # If the previous_assigned_user exists and is in the team
        if previous_assigned_user and previous_assigned_user.id in user_ids:
            previous_index = user_ids.index(previous_assigned_user.id)
            new_user = new_user.browse(user_ids[(previous_index + 1) % len(user_ids)])
        else:
            new_user = new_user.browse(user_ids[0])

        return new_user

    def _assign_balanced(self, user_ids, new_user):
        # Count open tickets per user
        read_group_res = self.env["helpdesk.ticket"].read_group(
            [("stage_id.closed", "=", False), ("user_id", "in", user_ids)],
            ["user_id"],
            ["user_id"],
        )

        # Initialize counts for all users, including those with zero open tickets
        count_dict = {m_id: 0 for m_id in user_ids}
        count_dict.update(
            (data["user_id"][0], data["user_id_count"]) for data in read_group_res
        )

        # Find the user with the minimum number of open tickets
        new_user = new_user.browse(min(count_dict, key=count_dict.get))

        return new_user
