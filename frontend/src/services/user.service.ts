import { userApi, type UserInfo } from "@/api/user.api";

export type MeDto = {
    id: number;
    email: string;
};

export async function getMe(): Promise<MeDto> {
    const envelope = await userApi.me();

    const data = envelope?.data;
    if (!data) {
        throw new Error("invalid_me_response");
    }
    const meDto: MeDto = {
        id: data.id,
        email: data.email,
    };

    return meDto;
}