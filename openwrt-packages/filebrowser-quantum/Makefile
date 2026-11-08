include $(TOPDIR)/rules.mk

PKG_NAME:=filebrowser-quantum
PKG_VERSION:=2.0.2
PKG_RELEASE:=1
PKG_SOURCE:=linux-arm64-filebrowser
PKG_SOURCE_URL:=https://github.com/gtsteffaniak/filebrowser/releases/download/v$(PKG_VERSION)-stable
PKG_HASH:=03eac074efc1b0ef3cb39882c04eeee26027049d261b6b6706650d4ac2d8e21c
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BUILD_PARALLEL:=1
PKG_LICENSE:=Apache-2.0
PKG_LICENSE_FILES:=LICENSE

include $(INCLUDE_DIR)/package.mk

define Package/filebrowser-quantum
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=FileBrowser Quantum web file manager
  URL:=https://github.com/gtsteffaniak/filebrowser
  LICENSE:=$(PKG_LICENSE)
  DEPENDS:=+ca-bundle
endef

define Package/filebrowser-quantum/description
  A self-hosted web file manager for browsing and managing files on USB storage.
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	cp $(DL_DIR)/$(PKG_SOURCE) $(PKG_BUILD_DIR)/filebrowser
endef

define Build/Compile
endef

define Package/filebrowser-quantum/conffiles
/etc/filebrowser-quantum/config.yaml
endef

define Package/filebrowser-quantum/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/filebrowser-quantum/cache
	$(INSTALL_DIR) $(1)/etc/init.d $(1)/etc/rc.d
	$(INSTALL_DIR) $(1)/usr/share/licenses/filebrowser-quantum
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/filebrowser $(1)/usr/bin/filebrowser-quantum
	$(INSTALL_CONF) ./files/config.yaml $(1)/etc/filebrowser-quantum/config.yaml
	$(INSTALL_BIN) ./files/filebrowser-quantum.init $(1)/etc/init.d/filebrowser-quantum
	$(INSTALL_DATA) ./files/LICENSE $(1)/usr/share/licenses/filebrowser-quantum/LICENSE
	$(LN) ../init.d/filebrowser-quantum $(1)/etc/rc.d/S95filebrowser-quantum
endef

$(eval $(call BuildPackage,filebrowser-quantum))
