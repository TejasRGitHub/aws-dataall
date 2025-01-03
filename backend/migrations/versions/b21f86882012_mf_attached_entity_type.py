"""mf_attached_entity_type

Revision ID: b21f86882012
Revises: 5a798acc6282
Create Date: 2024-10-22 15:50:42.652910

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm

from dataall.modules.metadata_forms.db.metadata_form_models import AttachedMetadataForm

# revision identifiers, used by Alembic.
revision = 'b21f86882012'
down_revision = '5a798acc6282'
branch_labels = None
depends_on = None


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    session = get_session()
    print('Rename entityType from Dataset to S3-Dataset for attached metadataform entries')
    all_amf = session.query(AttachedMetadataForm).all()
    for amf in all_amf:
        if amf.entityType == 'Dataset':
            amf.entityType = 'S3-Dataset'
    session.commit()
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    session = get_session()
    print('Rename entityType from S3-Dataset to Dataset for attached metadataform entries')
    all_amf = session.query(AttachedMetadataForm).all()
    for amf in all_amf:
        if amf.entityType == 'S3-Dataset':
            amf.entityType = 'Dataset'
    session.commit()
    # ### end Alembic commands ###
