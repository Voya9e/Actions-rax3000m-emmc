#!/bin/sh
set -eu

# Resolve both explicitly named bridges and Docker's generated br-<id> names.
driver="$(docker network inspect --format '{{.Driver}}' vidbee)"
[ "$driver" = bridge ] || {
    logger -t vidbee-firewall "VidBee must use a Docker bridge network"
    exit 1
}
bridge="$(docker network inspect --format '{{index .Options "com.docker.network.bridge.name"}}' vidbee)"
case "$bridge" in
    ''|'<no value>'|'<nil>')
        network_id="$(docker network inspect --format '{{.Id}}' vidbee)"
        case "$network_id" in
            ''|*[!0-9a-f]*) exit 1 ;;
        esac
        [ "${#network_id}" -eq 64 ] || exit 1
        bridge="br-$(printf '%s' "$network_id" | cut -c1-12)"
        ;;
esac
case "$bridge" in
    ''|*[!a-zA-Z0-9_.:-]*) exit 1 ;;
esac
[ "${#bridge}" -le 15 ] || exit 1

firewall_state() {
    uci -q show firewall.rax3000m_vidbee_zone || true
    uci -q show firewall.rax3000m_vidbee_lan || true
    uci -q show firewall.rax3000m_vidbee_wan || true
}

before="$(firewall_state)"
uci -q set firewall.rax3000m_vidbee_zone=zone
uci -q set firewall.rax3000m_vidbee_zone.name=vidbee
uci -q set "firewall.rax3000m_vidbee_zone.device=$bridge"
uci -q set firewall.rax3000m_vidbee_zone.input=REJECT
uci -q set firewall.rax3000m_vidbee_zone.output=ACCEPT
uci -q set firewall.rax3000m_vidbee_zone.forward=REJECT

# Docker performs DNAT; fw4 must also allow the forwarded container ports.
uci -q set firewall.rax3000m_vidbee_lan=rule
uci -q set 'firewall.rax3000m_vidbee_lan.name=Allow-LAN-VidBee'
uci -q set firewall.rax3000m_vidbee_lan.src=lan
uci -q set firewall.rax3000m_vidbee_lan.dest=vidbee
uci -q set firewall.rax3000m_vidbee_lan.proto=tcp
uci -q set 'firewall.rax3000m_vidbee_lan.dest_port=3000 3100'
uci -q set firewall.rax3000m_vidbee_lan.family=ipv4
uci -q set firewall.rax3000m_vidbee_lan.target=ACCEPT

uci -q set firewall.rax3000m_vidbee_wan=forwarding
uci -q set firewall.rax3000m_vidbee_wan.src=vidbee
uci -q set firewall.rax3000m_vidbee_wan.dest=wan
after="$(firewall_state)"
uci -q commit firewall
applied_file=/var/run/vidbee-firewall.applied
applied="$(cat "$applied_file" 2>/dev/null || true)"
if [ "$before" != "$after" ] || [ "$applied" != "$after" ]; then
    /etc/init.d/firewall reload
    printf '%s\n' "$after" > "$applied_file"
    logger -t vidbee-firewall "Enabled LAN access to VidBee on TCP 3000/3100 via $bridge"
fi
