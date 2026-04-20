"""Testes do módulo de plataformas."""

import pytest

from udemy_transcripter.platforms import (
    UdemyPlatform,
    detect_platform,
    get_platform,
)


class TestUdemyPlatform:
    def test_info(self):
        p = UdemyPlatform()
        info = p.info()
        assert info.name == "Udemy"
        assert "udemy.com" in info.base_url
        assert info.requires_auth is True

    def test_extract_slug_full_url(self):
        p = UdemyPlatform()
        assert p.extract_slug("https://www.udemy.com/course/docker-basico/") == "docker-basico"

    def test_extract_slug_with_params(self):
        p = UdemyPlatform()
        assert p.extract_slug("https://www.udemy.com/course/python-pro/?couponCode=ABC") == "python-pro"

    def test_extract_slug_plain(self):
        p = UdemyPlatform()
        assert p.extract_slug("docker-basico") == "docker-basico"

    def test_matches_url_true(self):
        p = UdemyPlatform()
        assert p.matches_url("https://www.udemy.com/course/algo/") is True

    def test_matches_url_false(self):
        p = UdemyPlatform()
        assert p.matches_url("https://www.alura.com.br/curso/algo") is False


class TestGetPlatform:
    def test_udemy(self):
        p = get_platform("udemy")
        assert isinstance(p, UdemyPlatform)

    def test_case_insensitive(self):
        p = get_platform("UDEMY")
        assert isinstance(p, UdemyPlatform)

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="não suportada"):
            get_platform("coursera")


class TestDetectPlatform:
    def test_detects_udemy(self):
        p = detect_platform("https://www.udemy.com/course/docker/")
        assert isinstance(p, UdemyPlatform)

    def test_fallback_to_udemy(self):
        # URLs desconhecidas caem no fallback Udemy
        p = detect_platform("https://www.alura.com.br/curso/algo")
        assert isinstance(p, UdemyPlatform)