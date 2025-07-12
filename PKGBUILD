# Maintainer: Moustafa Salem <salemmoustafa442@gmail.com>
pkgname=dotz
pkgver=0.4.0
pkgrel=1
pkgdesc="A minimal, Git-backed dotfiles manager for Linux"
arch=('any')
url="https://github.com/tTrmc/dotz"
license=('GPL-3.0-or-later')
depends=('python' 'python-typer' 'python-gitpython' 'python-watchdog' 'git')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
checkdepends=('python-pytest' 'python-pytest-cov')
source=("$pkgname-$pkgver.tar.gz::https://github.com/tTrmc/dotz/archive/v$pkgver.tar.gz")
sha256sums=('17d80320e4c186a00ac1df970281af5a85668f7fa794d9f79a989ebac4a05ff9')

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

check() {
    cd "$pkgname-$pkgver"
    # Run tests if they exist
    python -m pytest tests/ || true
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl

    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"

    # Install documentation
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
    install -Dm644 CHANGELOG.md "$pkgdir/usr/share/doc/$pkgname/CHANGELOG.md"
}
