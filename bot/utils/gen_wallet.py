from pycardano import PaymentVerificationKey, PaymentSigningKey, Address, StakeKeyPair

from configs.config import (
    KEYS_DIR,
    NETWORK,
)


def create_signing_key(name: str):
    """
    Creates a signing key, verification key, and address.
    """
    KEYS_DIR.mkdir(exist_ok=True)
    skey_path = KEYS_DIR.joinpath(f"{name}.skey")
    vkey_path = KEYS_DIR.joinpath(f"{name}.vkey")

    staking_skey = KEYS_DIR.joinpath(f"{name}.staking.skey")
    staking_vkey = KEYS_DIR.joinpath(f"{name}.staking.vkey")

    addr_path = KEYS_DIR.joinpath(f"{name}.addr")

    if skey_path.exists():
        raise FileExistsError(f"Signing key file ${skey_path} already exists")
    if vkey_path.exists():
        raise FileExistsError(f"Verification key file ${vkey_path} already exists")
    if addr_path.exists():
        raise FileExistsError(f"Address file ${addr_path} already exists")

    signing_key = PaymentSigningKey.generate()
    signing_key.save(str(skey_path))

    verification_key = PaymentVerificationKey.from_signing_key(signing_key)
    verification_key.save(str(vkey_path))

    staking_key = StakeKeyPair.generate()

    staking_singing_key = staking_key.signing_key
    staking_singing_key.save(str(staking_skey))

    staking_verification_key = staking_key.verification_key
    staking_verification_key.save(str(staking_vkey))

    address = Address(
        payment_part=verification_key.hash(),
        staking_part=staking_verification_key.hash(),
        network=NETWORK,
    )

    with open(addr_path, mode="w") as f:
        f.write(str(address))

    print(f"Wrote signing key to: {skey_path}")
    print(f"Wrote verification key to: {vkey_path}")
    print(f"Wrote address to: {addr_path}")
    print("Please fund the addresses to use them.")
