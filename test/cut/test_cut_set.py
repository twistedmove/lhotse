from tempfile import NamedTemporaryFile

import pytest

from lhotse import SupervisionSegment
from lhotse.cut import Cut, CutSet, MixedCut, MixTrack


@pytest.fixture
def cut_set_with_mixed_cut(cut1, cut2):
    mixed_cut = MixedCut(id='mixed-cut-id', tracks=[
        MixTrack(cut=cut1),
        MixTrack(cut=cut2, offset=1.0, snr=10)
    ])
    return CutSet({cut.id: cut for cut in [cut1, cut2, mixed_cut]})


def test_cut_set_iteration(cut_set_with_mixed_cut):
    cuts = list(cut_set_with_mixed_cut)
    assert len(cut_set_with_mixed_cut) == 3
    assert len(cuts) == 3


def test_cut_set_holds_both_simple_and_mixed_cuts(cut_set_with_mixed_cut):
    simple_cuts = cut_set_with_mixed_cut.simple_cuts.values()
    assert all(isinstance(c, Cut) for c in simple_cuts)
    assert len(simple_cuts) == 2
    mixed_cuts = cut_set_with_mixed_cut.mixed_cuts.values()
    assert all(isinstance(c, MixedCut) for c in mixed_cuts)
    assert len(mixed_cuts) == 1


@pytest.mark.parametrize(
    ['format', 'compressed'],
    [
        ('yaml', False),
        ('yaml', True),
        ('json', False),
        ('json', True),
    ]
)
def test_simple_cut_set_serialization(cut_set, format, compressed):
    with NamedTemporaryFile(suffix='.gz' if compressed else '') as f:
        if format == 'yaml':
            cut_set.to_yaml(f.name)
            restored = CutSet.from_yaml(f.name)
        if format == 'json':
            cut_set.to_json(f.name)
            restored = CutSet.from_json(f.name)
    assert cut_set == restored


@pytest.mark.parametrize(
    ['format', 'compressed'],
    [
        ('yaml', False),
        ('yaml', True),
        ('json', False),
        ('json', True),
    ]
)
def test_mixed_cut_set_serialization(cut_set_with_mixed_cut, format, compressed):
    with NamedTemporaryFile(suffix='.gz' if compressed else '') as f:
        if format == 'yaml':
            cut_set_with_mixed_cut.to_yaml(f.name)
            restored = CutSet.from_yaml(f.name)
        if format == 'json':
            cut_set_with_mixed_cut.to_json(f.name)
            restored = CutSet.from_json(f.name)
    assert cut_set_with_mixed_cut == restored


def test_filter_cut_set(cut_set, cut1):
    filtered = cut_set.filter(lambda cut: cut.id == 'cut-1')
    assert len(filtered) == 1
    assert list(filtered)[0] == cut1


def test_trim_to_unsupervised_segments():
    cut_set = CutSet.from_cuts([
        # Yields 3 unsupervised cuts - before first supervision,
        # between sup2 and sup3, and after sup3.
        Cut('cut1', start=0, duration=30, channel=0, supervisions=[
            SupervisionSegment('sup1', 'rec1', start=1.5, duration=8.5),
            SupervisionSegment('sup2', 'rec1', start=10, duration=5),
            SupervisionSegment('sup3', 'rec1', start=20, duration=8),
        ]),
        # Does not yield any "unsupervised" cut.
        Cut('cut2', start=0, duration=30, channel=0, supervisions=[
            SupervisionSegment('sup4', 'rec1', start=0, duration=30),
        ]),
    ])
    unsupervised_cuts = cut_set.trim_to_unsupervised_segments()

    assert len(unsupervised_cuts) == 3

    assert unsupervised_cuts[0].start == 0
    assert unsupervised_cuts[0].duration == 1.5
    assert unsupervised_cuts[0].supervisions == []

    assert unsupervised_cuts[1].start == 15
    assert unsupervised_cuts[1].duration == 5
    assert unsupervised_cuts[1].supervisions == []

    assert unsupervised_cuts[2].start == 28
    assert unsupervised_cuts[2].duration == 2
    assert unsupervised_cuts[2].supervisions == []
