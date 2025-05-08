#!/bin/bash

# This script downloads class materials from Google Docs and saves them as PDFs.

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    echo "\033[0;31mError: No internet connection. Please check your network settings."
    exit 1
fi

mkdir -p "$HOME/offline_materials/per"
mkdir -p "$HOME/offline_materials/bpc"
mkdir -p "$HOME/offline_materials/ipc"
mkdir -p "$HOME/offline_materials/apc"
mkdir -p "$HOME/offline_materials/sa"

per=(
    "[1 Dedication of Offerings](https://docs.google.com/document/d/1hBa7NGk8IaNqHDZlL-ZY-N86Fvh_qhQ8_N5veea-b04/)|"
    "[2 Preliminary Homage](https://docs.google.com/document/d/1qs2YbSMxL9-JWrfmiHiQvrI8uXDLGWxtN_GuON9QNHI/)|"
    "[3 Homage to the Buddha](https://docs.google.com/document/d/1G0cf4f_yaFlyAOfrPMnQAmtwpT2rzkHN48DwTomih0U/)|"
    "[4 Homage to the Dhamma](https://docs.google.com/document/d/1__RKdOoq-VLAv_M-ccaYxFhQfE4Jyesi4mMLJp13etE/)|"
    "[5 Homage to the Saṅgha](https://docs.google.com/document/d/1H7zzd88MbMt0E2FQQCYUYmWkkEzqmEtnylzrW6bsDZA/)|"
    "[6 Salutation to the Triple Gem](https://docs.google.com/document/d/1FZritL3lekZ03J18QaES2qQO2PNA8_CoUbroAgpspOs/)|"

    "[7 The Buddha’s First Exclamation](https://docs.google.com/document/d/1UFig1lS1oYwvJ5uQ3nnugGIvqaBq7aOe7xMRdVOA1tQ/)|"
    "[8 Respect for the Dhamma](https://docs.google.com/document/d/1CDTtwFmcyBJqrIQwROcMsqM8qXGzvyc5SFZjKOLaTXs/)|"
    "[9 Going to True and False Refuges](https://docs.google.com/document/d/1JAn5R2GYxBIYydbgKRHj1SbTelKfW8zn8Y2eeQTJ3j8/)|"
    "[10 The Pāṭimokkha Exhortation](https://docs.google.com/document/d/1DRd--uBllLKAIX45M0zpVcGaC3km5QQAfGw4hlJXPkw/)|"
    "[11 The Three Characteristics](https://docs.google.com/document/d/1O-gl_VRZgcaNk-xAr4HdGfm8-cj1SB5GksOQEtH7hrw/)|"
    "[12 The Burdens](https://docs.google.com/document/d/1vA6BoYgbZI-aZmrl6ycQYn3OA7V15C1FxuskJ99KvqA/)|"
    "[13 From the Elder Raṭṭhapāla](https://docs.google.com/document/d/10_48SNuskQ4Kca6GitWP1KMDUGFGrt4YK0X9nFTQw2I/)|"
    "[14 From the Elder Pārāpariya](https://docs.google.com/document/d/17HAQkJVQCbO17uxjdykiPNCCtr8UAG6wbnC77mXKyFM/)|"
    "[15 On Protection](https://docs.google.com/document/d/14MHZEf2m20r5JaIeGy3wr-tW7y5bFd8097_e1GfGdzQ/)|"
    "[16 Miscellaneous Verses](https://docs.google.com/document/d/1iX2GcszvFqjhwIaEstFGWQUMPyj-ZLCu9aJ5XZ6Mw9g/)|"
    "[17 A single Excellent Night](https://docs.google.com/document/d/1r2_xKy7oZ37tCIQEka2VJDEhebVCbRXkPGsVxUNd854/)|"

    "[18 Setting in Motion The Wheel of Dhamma](https://docs.google.com/document/d/1hfC4NyprTtz5cUzTEpSTYIal9ISo865T1J6UFqndRHM/)|"
    "[19 The Gradual Training](https://docs.google.com/document/d/1iBdxJtAW7hi7ZJ_9mSdFNjRbEo7s6v6FiR4Bn_1QKn4/)|"
    "[20 Requisites for Awakening](https://docs.google.com/document/d/1nRjJxWbGezi59s0DxfDBLTjX1dHdTSKWXD5EdzzZ5Us/)|"
    "[21 The Seven Factors of Awakening](https://docs.google.com/document/d/1rkmaVq4F5Gdij2Fx0EaV_sLZ0b4tmOAdK4KIMsb92xw/)|"
    "[22 The Noble Eightfold Path](https://docs.google.com/document/d/1iLE6dQYsOTB6SBYrynj4sdU5d0cucFdbN3-MdkT8BQ4/)|"
    "[23 Mindfulness of Breathing](https://docs.google.com/document/d/14YbehN068gRVLzkMOcJNLy_q3S7nmAM5v7NuGhEBypQ/)|"
    "[24 Dependent Origination](https://docs.google.com/document/d/1HPPHW8vBvmjBW4h-bh88LbKcax0Z0YQ6in-8FB4HnUA/)|"
    "[25 The Dhamma in Brief](https://docs.google.com/document/d/1rdNfUNiwEfSMfGoj2Kb85ZZXsrP-MwJlfvOs-PXaqsc/)|"
    "[26 The Four Great References](https://docs.google.com/document/d/1nNkWqfwM9bEZ-6SHqobisIPHIcMWqB08GbY62nxpugU/)|"
    "[27 Principles of Cordiality](https://docs.google.com/document/d/1Hye1mXDVZfVSejNz7vRzSbwAwfKgr4zXHtepvhzH0Vs/)|"
    "[28 Principles of Non-Decline](https://docs.google.com/document/d/1hx5Bltz4dm6VrAZeqB-8Rf9oz139BocrWriPtjsm5i0/)|"
    "[29 Striving According to the Dhamma](https://docs.google.com/document/d/1ZA6z8tv6mFZLEKmShP5DZxqqq8Rp8uT3SIscPloW3Ys/)|"
    "[30 The Buddha’s Final Instruction](https://docs.google.com/document/d/1eIuWXJAliDG0v-HpJUDRI7ZrlgNH4RfbE2marMrq38c/)|"

    "[31 The Four Requisites](https://docs.google.com/document/d/1azl8a1Y5kSXxYFKXc-R8c29J0J_NEBAtmXvSHIkY8zo/)|"
    "[32 The Repulsiveness of Food](https://docs.google.com/document/d/1bLJ3tYzSSWpfigqewEVIxtTq3H_9azz2Ch0CLZYOdzs/)|"
    "[33 Universal Well-Being](https://docs.google.com/document/d/1VlYGVeSDtx8tavnXCmgee4J6-Py3eH9DbJ2nwY23HNk/)|"
    "[34 The Divine Abidings](https://docs.google.com/document/d/1uOHGOyp_ydFd54V88oczlgnkBdJvD9pbNq42gauRm90/)|"
    "[35 Five Subjects for Frequent Recollection](https://docs.google.com/document/d/19nhhk-fkG8oUwE_mkNLV1ja_WmaskRqgKVaOreY8XSY/)|"
    "[36 Ten Subjects for Frequent Recollection by One Who Has Gone Forth](https://docs.google.com/document/d/1-6yapQqB0s7WdX7GijzXCeni5QmPhp4Xd7lVqovaNcA/)|"
    "[37 The Thirty-Two Parts](https://docs.google.com/document/d/193i-Z1sEgIkPK9YkBvn-TSMI7b-8QQIsbXqkN_cgZ2g/)|"
    "[38 Recollection of Impermanence](https://docs.google.com/document/d/1d59_2DrZ1axq39iXItJaI17oPnUd-tZ_8Heebu0bo9c/)|"

    "[39 Dhammacakkappavattana-sutta](https://docs.google.com/document/d/1Z3OEsxHS1bbuUqhU6jI0xWe7LPtJr3pfWUUmpsYG3Lw/)|"
    "[40 Anatta-lakkhaṇa-sutta](https://docs.google.com/document/d/1KUqsOrCtCGxZm9gvaBuQutMhv6N9ak0aJ-USkaGBjPc/)|"
    "[41 Āditta-pariyāya-sutta](https://docs.google.com/document/d/1noiUsphrtvNqz21Oqu7EcVFMOaQ93fcEYErqWbWdipk/)|"

    "[42 Yathā vāri-vahā](https://docs.google.com/document/d/1jl6cXyM2U9BJQ3AB-rdYzVPIi_deRHQrlkPJtWNxHHw/)|"
    "[43 Ratanattayānubhāv’ādi-gāthā](https://docs.google.com/document/d/1MyHG0kafRuRsLlSFDhcVCJrRyMDwXEBRNIyoB5MAGiE/)|"
    "[44 Bhojana-dānānumodanā](https://docs.google.com/document/d/1amk8x8220lTo3RsXYBr09waNd2Rii844vSOQxhZ1hko/)|"
    "[45 Culla-maṅgala-cakka-vāḷa](https://docs.google.com/document/d/11IhgUlqr0s29u2NmJP7yklHQ31VPdUUlTtLidwUM8rI/)|"
    "[46 Aggappasāda-sutta-gāthā](https://docs.google.com/document/d/1zLA7PLmN_uuhWQyzDRAyuGDcMZsTlnHbXSuvT4qyVbE/)|"
    "[47 Kāla-dāna-sutta-gāthā](https://docs.google.com/document/d/1smMeRSKEqTywbpTQexaVWwlM0ItftEwS9Fs9922ieJU/)|"
    "[48 So attha-laddho](https://docs.google.com/document/d/1iISQ3e2TaL4qS0jYmuu8qDzW2MxbGdPaLtTmDp2zwiw/)|"

    "[Word by Word Analysis of SBS Anumodana made by Ven. Ṭhanuttamo](https://docs.google.com/document/d/1qOjSvYnNt1FpMRZdq-vXRMQFH6uTdoYU5hWUN6AP5Hs/)|"

    "[49 Devā-ārādhanā](https://docs.google.com/document/d/1g85wBs0kuJF51coQzQSBOdfbqFewAi749Th9jJqaVhw/)|"
    "[50 Saraṇa-gamana-pāṭho](https://docs.google.com/document/d/1qarpYYFa8xjdol-gArglIkMiGg4jhIyrDmEafHDxnQM/)|"
    "[51 Nama-kāra-siddhi-gāthā](https://docs.google.com/document/d/1TqoCXbkwz4riPWFvy_ZO2v0kssEH_XqcaunthB1uXac/)|"
    "[52 Namo-kāra-aṭṭhaka](https://docs.google.com/document/d/1Y0drkOWgO2AKOHvWtnn2huc7QAyFyUSPZ_UzCJGnZZM/)|"
    "[53 Maṅgala-sutta](https://docs.google.com/document/d/1U96ujGucaUwKziqm0FNCg4u2e55oGH2ZGMP1IEsuZoQ/)|"
    "[54 Ratana-sutta](https://docs.google.com/document/d/1GE9J6Ws1ezWHxGQ5hJeFabPIoHONt7Gzrt86UNYNR4s/)|"
    "[55 Karaṇīya-metta-sutta](https://docs.google.com/document/d/1iLTSvK02-i-V2EfiMOXs_z8X-Tf2as06dVe2AuYBREo/)|"
    "[56 Khandha-parittaṃ](https://docs.google.com/document/d/1o2cDWXsgpJXm2d00woMNvsfk3Q35s5j9-DVV170bkgo/)|"
    "[57 Buddha-dhamma-saṅgha-guṇā](https://docs.google.com/document/d/19-2G8AGp2rzbPWVBwCoaVBmmYflR-nWfzTXruZLnhL0/)|"
    "[58 Yaṅ’kiñci ratanaṃ loke](https://docs.google.com/document/d/1tZRlAb7uXunf6WLBV8do4WfYvu5bSfgzRBoihH-TxAQ/)|"
    "[59 Bojjh’aṅga-parittaṃ](https://docs.google.com/document/d/1h7cHObJNGE9u5-CCT-LF7MkC1Q84Y1REf9KVBW6uW-U/)|"
    "[60 Abhaya-parittaṃ](https://docs.google.com/document/d/1EroYaPHLfct3o2lq6LKFHXU109N82ZRLK5LnWLqdHVE/)|"
    "[61 Devatā-uyyojana-gāthā](https://docs.google.com/document/d/1qQEYoxa_oRZmOnsoqttotDXwHXramcSz2taM4FLPRsA/)|"
    "[62 Jaya-maṅgala-aṭṭha-gāthā](https://docs.google.com/document/d/1XQQQ4hLZG2eZrMUxhLSrIK0VGnLhCIBKV84dLGyd7a4/)|"
    "[63 Jaya-parittaṃ](https://docs.google.com/document/d/17RA0WdLByrYBIYfh1d7Ls01W7bE6eBvWzVkHRLOe0nM/)|"
    "[64 Bhavatu-sabba-maṅgalaṃ](https://docs.google.com/document/d/1DS0c0ep8vLOUg1yUF0wVuWEZQpXe8WpkpHpQE2Jmb6I/)|"

    "[65 Dhamma-saṅgaṇī-mātikā](https://docs.google.com/document/d/1tAjTkFUMsVGKN7o7EpKHDZ360bs6Nae7m7Q8xwKYfng/)|"
    "[66 Vipassanā-bhūmi-pāṭho](https://docs.google.com/document/d/1cbIebgBU_PDgVP3lIRsirGy9mqnetkNXXVnpnKjEFXI/)|"
    "[67 Paṭṭhāna-mātikā-pāṭho](https://docs.google.com/document/d/1UZuznVdxRvvqdhjRk6gNjfmhnj3p14yVyziHmyKsy6c/)|"
    "[68 Adāsi-me ādi gāthā](https://docs.google.com/document/d/1DMMEOoykXO5Hjwl8D7lrG-F5jNvKoq2g_m2HZY6snsU/)|"
    "[69 Paṃsu-kūla](https://docs.google.com/document/d/1lxxbDwwp3j9D-LNlkwvfqX7oECJPQuiETAZ7F53Y2ag/)|"

    "[70 Sharing and Aspirations](https://docs.google.com/document/d/1nf7AbjIPgWQUwyaWWImr_0HT-mdMbXE_kiySAyS0RAg/)|"
    "[71 Sharing of All Merits](https://docs.google.com/document/d/1tXjzVuW0ezuEqgUEQnmoil1-RNYMBFGajjwrtB5LKi8/)|"
    "[72 Sharing of Merits with the Departed](https://docs.google.com/document/d/1p3BdcL0gXNHy9T1dXX-8AAHuOgxlpXjBMY8WLAwQUL4/)|"
    "[73 Sharing of Merits with the Devas](https://docs.google.com/document/d/1FEvRHPJWVAiMP94NSH6vKhyzSOb_EOX4Je1A-_Vg17c/)|"
    "[74 The Highest Honour and Aspirations](https://docs.google.com/document/d/1snej2MNlaEtPH-f_4Gv8YpFleifo-Uz3f17XEkbYUw4/)|"

    "[Post Pātimokkha recitations](https://docs.google.com/document/d/1Qzh_BTJgg-YSxGMyEyu1TciVSX_lVg3arSzD_Vtf_Fg/)|"
)

bpc=(
    "[Beginner Pāli Course](https://docs.google.com/document/d/1mXn2uQyPoFjpqKj5xKAPEFdb25pLwQ2yOxTiLeAh4_c/)|"
    "[BPC Exercises 1 - 7](https://docs.google.com/document/d/13BVDI3SSNqfd2gmv-cnUZynJ63es7-0TNkqXP95Wqb0/)|"
    "[BPC Exercises 8 - 11](https://docs.google.com/document/d/19u1_BuP1ovgjqGf8GWkCE2zlS977jnHE6MXHv5EPBXU/)|"
    "[BPC Exercises 12 - 15](https://docs.google.com/document/d/11QMWMTxnxkz5YeHnlxm1YJap2VxAeXTK9_j2F-6o5OI/)|"
    "[BPC Key to Exercises 01 - 7](https://docs.google.com/document/d/14ZtcfunRroZl5yvxQdUojMXOj83IAqhIWFUjw5hC2pY/)|"
    "[BPC Key to Exercises 08 - 11](https://docs.google.com/document/d/11qnZ0ZmhmCCMv8A8cypJbBEtTkJogwHapQevFFknukA/)|"
    "[BPC Key to Exercises 12 - 15](https://docs.google.com/document/d/1UfbHEn3KJxSWB1xQteULZmUOTvFONrgXoJ1tmm7Ma-Q/)|"
)

ipc=(
    "[Intermediate Pāli Course](https://docs.google.com/document/d/1K9UEl91eisxDjutTya-8bP8K4VcC1TD2cS6JEz4JAUE/)|"
    "[IPC Exercises 16 - 19](https://docs.google.com/document/d/1fWI28PgTLUVqGn-c0jnAFp_9-6cYg9M4AwmjmmRJrfw/)|"
    "[IPC Exercises 20 - 24](https://docs.google.com/document/d/1tzD2ZO4NdgrVjsGBAX-sb9LdEnmkAhI9LuJvyi25vVg/)|"
    "[IPC Exercises 25 - 29](https://docs.google.com/document/d/1H1UX8RvHcE1AViRgRz_PDo4PtwoED28vyh2zuZKgjNE/)|"
    "[IPC Key to Exercises 16 - 19](https://docs.google.com/document/d/10k828FOENjhbYtu7EAD3xuuAX4EOSSmhciIXmAbP2qw/)|"
    "[IPC Key to Exercises 20 - 24](https://docs.google.com/document/d/1RK3BFVPlRoJZMvCOYGvU3fUW0EdLbPrtztjQACxbybA/)|"
    "[IPC Key to Exercises 25 - 29](https://docs.google.com/document/d/1afXpWDCOCeS9WlbmjaMFDhonlCdbV5PHh-kJoE5WKig/)|"
)

apc=(
    "[Advanced Pāli Course](https://docs.google.com/document/d/1QMX_yuH9uJeTEfg3ItetlI5RVsPGlj0Q1XUstHXRLZo/)|"
    "[APC Key to Exercises 30 - 39](https://docs.google.com/document/d/1VoFPr2jqJbQEQgT_UbuhxpzHM_H_mqX3BCy3vMdqiUc/)|"
    "[APC Key to Exercises 40 - 50](https://docs.google.com/document/d/1c5E1-xA5OEKOC_myMBqVzdcEkoyiqfurAphMLz7JmnQ/)|"
    "[APC Key to idioms and difficult passages](https://docs.google.com/document/d/18IBPFP0zs3ngEV-Ps5MmiGwaFtuz_2r3AqsZBlksPIQ/)|"
)

sa=(
    "[pubbakicca Dhammayuttika](https://docs.google.com/document/d/1z4B3TELrZlVemxP_gB0ciampFTIOS5hL/)|"

    "[1. MN 107 gaṇakamoggallānasuttaṁ](https://docs.google.com/document/d/1oW92myGIHzLypzNQGQPa0YeTGDfVq_Aogre8sLTRQuM/)|"

    "[2. Sacca Saṁyutta (SN 56)](https://docs.google.com/document/d/1QvmDByxRI4hMT3C8EqrafaGoXC5HA_8kRn730-VtKjY/)|"
    "[3. Khandha Saṁyutta (SN 22)](https://docs.google.com/document/d/1kt-OP0fUHEjR4pmc72ZljK8XD9oirssI1fMvfTvOhKw/)|"
    "[4. Saḷāyatana Saṁyutta (SN 35)](https://docs.google.com/document/d/1uyOA--pUQlHTzs1GWFQHorXkeVkwBEmJdWmPMBWoBXc/)|"
    "[5. Nidāna Saṃyutta (SN 12)](https://docs.google.com/document/d/1rSgxc6Hg8Pt63nU1fdG8j7QpobBRYbeDEE9KoZ9c6UQ/)|"
    "[6. Satipaṭṭhāna Saṃyutta (SN 47)](https://docs.google.com/document/d/1h-Xhkskz1-gchNBDG08QQJ-AqUs-sIimSBnDizvMibQ/)|"
    "[7. Bojjhaṅgasaṃyutta Saṃyutta (SN 46)](https://docs.google.com/document/d/11674RA0aMFbJuzdJ8LpVQIb3FRXRuoVRuWZ7IPA70Xc/)|"
    "[8. Maggasaṃyutta Saṃyutta (SN 45)](https://docs.google.com/document/d/1Efn0qcwgBoVdtx9GfU9Ia9lQYwMgYAjNvDyUVH9RlnM/)|"
    "[9. Asaṅkhata Saṃyutta (SN 43)](https://docs.google.com/document/d/1yDVS30Mha1T5cQ0-AkDW0_LJ2QhDU-3tdrBq7byKJ5w/)|"

)

cd "$HOME/offline_materials"

# Loop through the list of per and extract the title and URL
for link in "${per[@]}"; do
    # Extract title from within square brackets
    title=$(echo "$link" | sed -n 's/\[\([^]]*\)\].*/\1/p')
    # Extract URL from within parentheses
    url=$(echo "$link" | sed -n 's/.*(\(https:[^)]*\)).*/\1/p' | sed 's/\/$//')

    # Generate and execute the curl command with the formatted title
    curl -L "$url/export?format=pdf" -o "per/$title.pdf"

    # Check if the downloaded file exists
    if [ ! -f "per/$title.pdf" ]; then
        echo "\033[0;31mError: $title.pdf not available at $url\033[0m"
        exit 1
    fi
done

# Loop through the list of bpc and extract the title, URL, and folder
for link in "${bpc[@]}"; do
    # Extract title from within square brackets
    title=$(echo "$link" | sed -n 's/\[\([^]]*\)\].*/\1/p')
    # Extract URL from within parentheses
    url=$(echo "$link" | sed -n 's/.*(\(https:[^)]*\)).*/\1/p' | sed 's/\/$//')

    # Generate and execute the curl command with the formatted title
    curl -L "$url/export?format=pdf" -o "bpc/$title.pdf"

    # Check if the downloaded file exists
    if [ ! -f "bpc/$title.pdf" ]; then
        echo "\033[0;31mError: $title.pdf not available at $url\033[0m"
        exit 1
    fi
done

# Loop through the list of ipc and extract the title, URL, and folder
for link in "${ipc[@]}"; do
    # Extract title from within square brackets
    title=$(echo "$link" | sed -n 's/\[\([^]]*\)\].*/\1/p')
    # Extract URL from within parentheses
    url=$(echo "$link" | sed -n 's/.*(\(https:[^)]*\)).*/\1/p' | sed 's/\/$//')

    # Generate and execute the curl command with the formatted title
    curl -L "$url/export?format=pdf" -o "ipc/$title.pdf"

    # Check if the downloaded file exists
    if [ ! -f "ipc/$title.pdf" ]; then
        echo "\033[0;31mError: $title.pdf not available at $url\033[0m"
        exit 1
    fi
done

# Loop through the list of apc and extract the title, URL, and folder
for link in "${apc[@]}"; do
    # Extract title from within square brackets
    title=$(echo "$link" | sed -n 's/\[\([^]]*\)\].*/\1/p')
    # Extract URL from within parentheses
    url=$(echo "$link" | sed -n 's/.*(\(https:[^)]*\)).*/\1/p' | sed 's/\/$//')

    # Generate and execute the curl command with the formatted title
    curl -L "$url/export?format=pdf" -o "apc/$title.pdf"

    # Check if the downloaded file exists
    if [ ! -f "apc/$title.pdf" ]; then
        echo "\033[0;31mError: $title.pdf not available at $url\033[0m"
        exit 1
    fi
done

# Loop through the list of sa and extract the title, URL, and folder
for link in "${sa[@]}"; do
    # Extract title from within square brackets
    title=$(echo "$link" | sed -n 's/\[\([^]]*\)\].*/\1/p')
    # Extract URL from within parentheses
    url=$(echo "$link" | sed -n 's/.*(\(https:[^)]*\)).*/\1/p' | sed 's/\/$//')

    # Generate and execute the curl command with the formatted title
    curl -L "$url/export?format=pdf" -o "sa/$title.pdf"

    # Check if the downloaded file exists
    if [ ! -f "sa/$title.pdf" ]; then
        echo "\033[0;31mError: $title.pdf not available at $url\033[0m"
        exit 1
    fi
done

# Check if the fileserver is mounted
if [ -d "$HOME/filesrv1/share1/Sharing between users" ]; then

    echo "Copying folders to the fileserver"

    # Copy folders on the server
    cp -X -rf bpc/* "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/offline materials/beginner/"

    cp -X -rf ipc/* "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/offline materials/intermediate/"

    cp -X -rf apc/* "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/offline materials/advanced/"

    cp -X -rf sa/* "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/offline materials/suttas alalysis/"

    cp -X -rf per/* "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/offline materials/PER analysis/"

    echo "Copied folders to the fileserver"

else
    echo "Fileserver is not mounted. Skipping copying folders."
fi

# Combine and clean materials to txt
# cd "$HOME/.local/bin"
# bash make_comb_class.sh
# bash make_comb_suttas.sh

# Check if any errors occurred during the script execution
if [ $? -ne 0 ]; then
    echo "\033[0;31mError: Some PDFs were not available or an error occurred during the script execution.\033[0m"
fi
