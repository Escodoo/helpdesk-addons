# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res.get("team_id"):
            update_vals = self._onchange_team_get_values(
                self.env["helpdesk.ticket.team"].browse(res["team_id"])
            )
            if (not fields or "user_id" in fields) and "user_id" not in res:
                res["user_id"] = update_vals["user_id"]
        return res

    def _onchange_team_get_values(self, team):
        return {
            "user_id": team.get_new_user().id,
        }

    @api.onchange("team_id")
    def _onchange_team_id(self):
        if self.team_id:
            update_vals = self._onchange_team_get_values(self.team_id)
            if not self.user_id:
                self.user_id = update_vals["user_id"]

    @api.model
    def create(self, vals):
        if vals.get("team_id"):
            vals.update(
                item
                for item in self._onchange_team_get_values(
                    self.env["helpdesk.ticket.team"].browse(vals["team_id"])
                ).items()
                if item[0] not in vals
            )
        return super(HelpdeskTicket, self.with_context(mail_create_nolog=True)).create(
            vals
        )
