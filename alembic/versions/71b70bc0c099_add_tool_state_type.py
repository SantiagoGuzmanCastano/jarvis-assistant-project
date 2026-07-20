"""add tool state type

Revision ID: 71b70bc0c099
Revises: 83245765c129
Create Date: 2026-07-19 22:17:09.252152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71b70bc0c099'
down_revision: Union[str, Sequence[str], None] = '83245765c129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("conversation_tool_state",sa.Column("state_type", sa.String(), nullable=True))

    #fijate bien lo que hace esta linea, al momento de guardar un tool state, se retira el state type
    #del payload y se mete a un campo nuevo de la tabla y el payload queda solo con el payload, no con el state type
    op.execute(
        """
        UPDATE conversation_tool_state
        SET
            state_type = payload_json->>'state_type',
            payload_json = payload_json - 'state_type'
        WHERE payload_json ? 'state_type'
        """
    )

    op.alter_column(
        "conversation_tool_state",
        "state_type",
        existing_type=sa.String(),
        nullable=False,
    )

def downgrade() -> None:
    op.execute(
        """
        UPDATE conversation_tool_state
        SET payload_json = jsonb_build_object('state_type', state_type) || payload_json
        """
    )

    op.drop_column("conversation_tool_state", "state_type")