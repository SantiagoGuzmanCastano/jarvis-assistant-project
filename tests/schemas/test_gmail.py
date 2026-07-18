import pytest
from pydantic import ValidationError

from app.schemas.tools.gmail import (
    CreateDraftArguments,
    CreateMultipleDraftsArguments,
    DraftListArguments,
    MoveEmailToTrashArguments,
    ReadLatestEmailArguments,
    ReadSpecificEmailArguments,
    UpdateDraftArguments,
)


def test_read_specific_email_arguments_applies_search_defaults() -> None:
    arguments = ReadSpecificEmailArguments()

    assert arguments.search_keywords == []
    assert arguments.sender_hint == []
    assert arguments.max_results == 3
    assert arguments.requested_result_count == 1
    assert arguments.selected_result_position is None


def test_read_specific_email_arguments_rejects_invalid_position() -> None:
    with pytest.raises(ValidationError) as error_info:
        ReadSpecificEmailArguments(selected_result_position=0)

    assert error_info.value.errors()[0]["loc"] == ("selected_result_position",)


def test_create_draft_arguments_requires_complete_valid_draft() -> None:
    with pytest.raises(ValidationError) as error_info:
        CreateDraftArguments(
            recipient_email="lina",
            subject="",
            body="",
        )

    invalid_fields = {error["loc"][0] for error in error_info.value.errors()}

    assert invalid_fields == {"recipient_email", "subject", "body"}


def test_create_draft_arguments_accepts_complete_valid_draft() -> None:
    arguments = CreateDraftArguments(
        recipient_email="lina@example.com",
        subject="Factura",
        body="Adjunto la factura.",
    )

    assert str(arguments.recipient_email) == "lina@example.com"


def test_create_multiple_drafts_arguments_accepts_incomplete_items() -> None:
    arguments = CreateMultipleDraftsArguments(
        to_create=2,
        to_create_list=[
            {
                "recipient_email": "lina@example.com",
                "subject": "Factura",
                "body": "Adjunto la factura.",
            },
            {
                "subject": "Sin destinatario",
            },
        ],
    )

    assert arguments.to_create_list[0].recipient_email == "lina@example.com"
    assert arguments.to_create_list[1].recipient_email is None
    assert arguments.to_create_list[1].body is None


def test_create_multiple_drafts_arguments_rejects_empty_list() -> None:
    with pytest.raises(ValidationError) as error_info:
        CreateMultipleDraftsArguments(to_create=1, to_create_list=[])

    assert error_info.value.errors()[0]["loc"] == ("to_create_list",)


def test_update_draft_arguments_requires_known_selection_source() -> None:
    with pytest.raises(ValidationError) as error_info:
        UpdateDraftArguments(selection_source="previous")

    assert error_info.value.errors()[0]["loc"] == ("selection_source",)


def test_move_email_to_trash_arguments_allows_multiple_requested_results() -> None:
    arguments = MoveEmailToTrashArguments(requested_result_count=2)

    assert arguments.requested_result_count == 2


def test_draft_list_arguments_rejects_more_than_five_results() -> None:
    with pytest.raises(ValidationError) as error_info:
        DraftListArguments(max_results=6)

    assert error_info.value.errors()[0]["loc"] == ("max_results",)


def test_read_latest_email_arguments_rejects_more_than_two_results() -> None:
    with pytest.raises(ValidationError) as error_info:
        ReadLatestEmailArguments(max_results=3)

    assert error_info.value.errors()[0]["loc"] == ("max_results",)
