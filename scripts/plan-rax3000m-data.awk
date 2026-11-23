# Read an sfdisk dump and plan partition 6 in the unused tail of the eMMC.
# disk_sectors comes from sysfs and is measured in 512-byte sectors.
function reject(reason) {
    print reason > "/dev/stderr"
    invalid = 1
}

BEGIN {
    count = split(kernel_layout, kernel_parts, ";")
    for (i = 1; i <= count; i++) {
        split(kernel_parts[i], geometry, ":")
        kernel_start[i] = geometry[1]
        kernel_size[i] = geometry[2]
    }
    expected_name[1] = "ubootenv"
    expected_name[2] = "factory"
    expected_name[3] = "fip"
    expected_name[4] = "recovery"
    expected_name[5] = "production"
    expected_start[1] = 8192
    expected_start[2] = 9216
    expected_start[3] = 13312
    expected_start[4] = 24576
    expected_start[5] = 131072
    expected_size[1] = 1024
    expected_size[2] = 4096
    expected_size[3] = 8192
    expected_size[4] = 65536
    if (disk_sectors !~ /^[0-9]+$/ || disk_sectors < 4194304)
        reject("Invalid eMMC size")
}

/^label: gpt$/ { gpt = 1 }
/^unit: sectors$/ { sectors = 1 }
/^sector-size: 512$/ { sector_size = 1 }
/^last-lba: [0-9]+$/ { last_lba_count++ }

/^\/dev\// {
    number = $1
    if (number !~ /^\/dev\/mmcblk0p[0-9]+$/) {
        reject("Unexpected partition device")
        next
    }
    sub(/^\/dev\/mmcblk0p/, "", number)
    number += 0
    if (seen[number]++) reject("Duplicate partition number")
    start = size = name = ""
    count = split($0, fields, ",")
    for (i = 1; i <= count; i++) {
        field = fields[i]
        if (field ~ /start=[[:space:]]*[0-9]+/) {
            sub(/^.*start=[[:space:]]*/, "", field)
            sub(/[[:space:]]*$/, "", field)
            start = field
        } else if (field ~ /size=[[:space:]]*[0-9]+/) {
            sub(/^.*size=[[:space:]]*/, "", field)
            sub(/[[:space:]]*$/, "", field)
            size = field
        } else if (field ~ /^[[:space:]]*name=/) {
            sub(/^[[:space:]]*name="/, "", field)
            sub(/"[[:space:]]*$/, "", field)
            name = field
        }
    }
    if (start !~ /^[0-9]+$/ || size !~ /^[0-9]+$/ || size < 1) {
        reject("Invalid partition geometry")
        next
    }
    start += 0
    size += 0
    if (number >= 1 && number <= 5) {
        if (name != expected_name[number] || start != expected_start[number])
            reject("Unrecognized RAX3000M partition layout")
        if (number < 5 && size != expected_size[number])
            reject("Unexpected boot partition size")
        if (number == 5 && size < 131072)
            reject("Production partition is too small")
        if (kernel_start[number] != start || kernel_size[number] != size)
            reject("GPT differs from the running kernel partition map")
    } else if (number == 128) {
        if (start != 34 || size != 8158)
            reject("Unexpected reserved partition")
    } else {
        reject("Additional partitions already occupy this disk")
    }
    end = start + size
    if (end > disk_sectors - 33) reject("Partition extends beyond the disk")
    if (end > tail_start) tail_start = end
}

END {
    if (!gpt || !sectors || !sector_size || last_lba_count != 1)
        reject("Expected a GPT with 512-byte sectors")
    for (i = 1; i <= 5; i++)
        if (!seen[i]) reject("Required boot partition is missing")
    # Leave one MiB at the end for the backup GPT and align both boundaries.
    start = int((tail_start + 2047) / 2048) * 2048
    end = int((disk_sectors - 2048) / 2048) * 2048
    if (end - start < 4194304)
        reject("Less than 2 GiB of contiguous tail space remains")
    if (invalid) exit 1
    printf "%.0f %.0f\n", start, end - start
}
